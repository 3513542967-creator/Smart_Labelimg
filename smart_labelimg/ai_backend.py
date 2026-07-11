from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Protocol

import cv2
import numpy as np

from smart_labelimg.annotation import Box


class SmartBoxBackend(Protocol):
    def detect_labels(self, image_path: Path, labels: list[str]) -> list[Box]:
        ...


def choose_compute_device(torch_module, requested: str | None = None) -> str:
    """Return a supported explicit device, defaulting safely to CPU."""
    choice = (requested or os.environ.get("SMART_LABELIMG_DEVICE", "auto")).lower()
    if choice not in {"auto", "cpu", "cuda", "mps"}:
        choice = "auto"
    if choice != "auto":
        return choice
    if torch_module.cuda.is_available():
        return "cuda"
    mps = getattr(torch_module.backends, "mps", None)
    return "mps" if mps and mps.is_available() else "cpu"

    def detect_from_click(self, image: np.ndarray, x: int, y: int, label: str) -> list[Box]:
        ...

    def refine_from_box(self, image: np.ndarray, query_box: tuple[int, int, int, int], label: str) -> list[Box]:
        ...

    def find_similar(self, image: np.ndarray, query_box: tuple[int, int, int, int], label: str) -> list[Box]:
        ...


class ClassicalVisionBackend:
    """Offline Mac-friendly backend for click boxes and similar-object proposals."""

    def detect_labels(self, image_path: Path, labels: list[str]) -> list[Box]:
        return []

    def detect_from_click(self, image: np.ndarray, x: int, y: int, label: str) -> list[Box]:
        if image.size == 0:
            return []
        height, width = image.shape[:2]
        if not (0 <= x < width and 0 <= y < height):
            return []

        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        clicked = lab[y, x].astype(np.int16)
        distance = np.linalg.norm(lab.astype(np.int16) - clicked, axis=2)
        mask = (distance < 28).astype(np.uint8) * 255
        mask = cv2.medianBlur(mask, 5)
        flood = np.zeros((height + 2, width + 2), dtype=np.uint8)
        filled = mask.copy()
        cv2.floodFill(filled, flood, (x, y), 127)
        component = (filled == 127).astype(np.uint8)

        contours, _ = cv2.findContours(component, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return []
        contour = max(contours, key=cv2.contourArea)
        if cv2.contourArea(contour) < 20:
            return []
        bx, by, bw, bh = cv2.boundingRect(contour)
        padded = self._pad_box((bx, by, bx + bw, by + bh), width, height, 2)
        return [Box(label, *padded, score=1.0)]

    def refine_from_box(self, image: np.ndarray, query_box: tuple[int, int, int, int], label: str) -> list[Box]:
        if image.size == 0:
            return []
        height, width = image.shape[:2]
        x1, y1, x2, y2 = self._clip_tuple(query_box, width, height)
        crop = image[y1:y2, x1:x2]
        if crop.size == 0 or crop.shape[0] < 3 or crop.shape[1] < 3:
            return []

        lab = cv2.cvtColor(crop, cv2.COLOR_RGB2LAB)
        border = np.concatenate((lab[0, :, :], lab[-1, :, :], lab[:, 0, :], lab[:, -1, :]), axis=0)
        background = np.median(border, axis=0)
        distance = np.linalg.norm(lab.astype(np.float32) - background.astype(np.float32), axis=2)
        mask = (distance > 24).astype(np.uint8) * 255
        mask = cv2.medianBlur(mask, 5)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return [Box(label, x1, y1, x2, y2, score=1.0).normalized()]
        contour = max(contours, key=cv2.contourArea)
        if cv2.contourArea(contour) < 20:
            return [Box(label, x1, y1, x2, y2, score=1.0).normalized()]
        bx, by, bw, bh = cv2.boundingRect(contour)
        padded = self._pad_box((x1 + bx, y1 + by, x1 + bx + bw, y1 + by + bh), width, height, 2)
        return [Box(label, *padded, score=1.0)]

    def find_similar(self, image: np.ndarray, query_box: tuple[int, int, int, int], label: str) -> list[Box]:
        height, width = image.shape[:2]
        x1, y1, x2, y2 = self._clip_tuple(query_box, width, height)
        template = image[y1:y2, x1:x2]
        if template.size == 0 or template.shape[0] < 8 or template.shape[1] < 8:
            return []

        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        template_lab = lab[y1:y2, x1:x2]
        mean = template_lab.reshape(-1, 3).mean(axis=0)
        distance = np.linalg.norm(lab.astype(np.float32) - mean.astype(np.float32), axis=2)
        mask = (distance < 30).astype(np.uint8) * 255
        mask = cv2.medianBlur(mask, 5)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        query_area = max(1, (x2 - x1) * (y2 - y1))
        candidates: list[Box] = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < query_area * 0.35 or area > query_area * 2.5:
                continue
            bx, by, bw, bh = cv2.boundingRect(contour)
            aspect = bw / max(1, bh)
            query_aspect = (x2 - x1) / max(1, y2 - y1)
            if not (query_aspect * 0.45 <= aspect <= query_aspect * 2.2):
                continue
            padded = self._pad_box((bx, by, bx + bw, by + bh), width, height, 2)
            candidates.append(Box(label, *padded, score=1.0))
        return self._non_max_suppression(candidates, iou_threshold=0.25)

    def _non_max_suppression(self, boxes: list[Box], iou_threshold: float) -> list[Box]:
        sorted_boxes = sorted(boxes, key=lambda box: box.score or 0, reverse=True)
        kept: list[Box] = []
        for box in sorted_boxes:
            if all(self._iou(box, other) < iou_threshold for other in kept):
                kept.append(box)
        return kept[:50]

    def _iou(self, a: Box, b: Box) -> float:
        ax1, ay1, ax2, ay2 = a.normalized().x1, a.normalized().y1, a.normalized().x2, a.normalized().y2
        bx1, by1, bx2, by2 = b.normalized().x1, b.normalized().y1, b.normalized().x2, b.normalized().y2
        ix1, iy1 = max(ax1, bx1), max(ay1, by1)
        ix2, iy2 = min(ax2, bx2), min(ay2, by2)
        inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
        union = a.width * a.height + b.width * b.height - inter
        return inter / union if union else 0.0

    def _pad_box(self, box: tuple[int, int, int, int], width: int, height: int, padding: int) -> tuple[int, int, int, int]:
        x1, y1, x2, y2 = box
        return (
            max(0, x1 - padding),
            max(0, y1 - padding),
            min(width - 1, x2 + padding),
            min(height - 1, y2 + padding),
        )

    def _clip_tuple(self, box: tuple[int, int, int, int], width: int, height: int) -> tuple[int, int, int, int]:
        x1, y1, x2, y2 = box
        x1, x2 = sorted((max(0, min(width - 1, x1)), max(0, min(width, x2))))
        y1, y2 = sorted((max(0, min(height - 1, y1)), max(0, min(height, y2))))
        return x1, y1, x2, y2


def mask_to_box(mask: np.ndarray, label: str, score: float | None = None) -> Box:
    ys, xs = np.where(mask)
    if len(xs) == 0 or len(ys) == 0:
        return Box(label, 0, 0, 0, 0, score)
    return Box(label, int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()), score)


@dataclass
class MobileSamBackend:
    checkpoint_path: str
    model_type: str = "vit_t"
    device: str | None = None

    def __post_init__(self) -> None:
        from mobile_sam import SamPredictor, sam_model_registry
        import torch

        self.device = choose_compute_device(torch, self.device)
        model = sam_model_registry[self.model_type](checkpoint=self.checkpoint_path)
        try:
            model.to(device=self.device)
        except (RuntimeError, AssertionError):
            if self.device == "cpu":
                raise
            # A driver can disappear or be incompatible after capability probing.
            # Recreate the model on CPU so the application remains usable.
            self.device = "cpu"
            model = sam_model_registry[self.model_type](checkpoint=self.checkpoint_path)
            model.to(device="cpu")
        model.eval()
        self.predictor = SamPredictor(model)

    def detect_labels(self, image_path: Path, labels: list[str]) -> list[Box]:
        return []

    def detect_from_click(self, image: np.ndarray, x: int, y: int, label: str) -> list[Box]:
        if image.size == 0:
            return []
        self.predictor.set_image(image)
        masks, scores, _ = self.predictor.predict(
            point_coords=np.array([[x, y]], dtype=np.float32),
            point_labels=np.array([1], dtype=np.int32),
            multimask_output=True,
        )
        if len(masks) == 0:
            return []
        areas = np.array([mask.sum() for mask in masks], dtype=np.float32)
        image_area = float(image.shape[0] * image.shape[1])
        valid = np.where((areas > 20) & (areas < image_area * 0.45))[0]
        if len(valid) == 0:
            valid = np.where(areas > 20)[0]
        if len(valid) == 0:
            return []
        max_score = float(scores[valid].max())
        near_best = valid[scores[valid] >= max_score - 0.12]
        best_index = int(near_best[np.argmax(areas[near_best])])
        mapped = mask_to_box(masks[best_index], label=label, score=float(scores[best_index])).clipped((image.shape[1], image.shape[0]))
        return [mapped] if mapped.width > 0 and mapped.height > 0 else []

    def refine_from_box(self, image: np.ndarray, query_box: tuple[int, int, int, int], label: str) -> list[Box]:
        height, width = image.shape[:2]
        x1, y1, x2, y2 = ClassicalVisionBackend()._clip_tuple(query_box, width, height)
        if x2 - x1 < 3 or y2 - y1 < 3:
            return []
        self.predictor.set_image(image)
        masks, scores, _ = self.predictor.predict(
            box=np.array([x1, y1, x2, y2], dtype=np.float32),
            multimask_output=True,
        )
        if len(masks) == 0:
            return []
        areas = np.array([mask.sum() for mask in masks], dtype=np.float32)
        valid = np.where(areas > 20)[0]
        if len(valid) == 0:
            return []
        best_index = int(valid[np.argmax(scores[valid])])
        mapped = mask_to_box(masks[best_index], label=label, score=float(scores[best_index])).clipped((width, height))
        return [mapped] if mapped.width > 0 and mapped.height > 0 else []

    def find_similar(self, image: np.ndarray, query_box: tuple[int, int, int, int], label: str) -> list[Box]:
        return ClassicalVisionBackend().find_similar(image, query_box, label)


@dataclass
class OnnxMobileSamBackend:
    encoder_path: str
    decoder_path: str
    device: str | None = None

    def __post_init__(self) -> None:
        import onnxruntime as ort

        options = ort.SessionOptions()
        options.enable_mem_pattern = False
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        available = ort.get_available_providers()
        force_cpu = (self.device or os.environ.get("SMART_LABELIMG_DEVICE", "auto")).lower() == "cpu"
        providers = ["CPUExecutionProvider"]
        if not force_cpu and "DmlExecutionProvider" in available:
            providers.insert(0, "DmlExecutionProvider")
        try:
            self.encoder = ort.InferenceSession(self.encoder_path, sess_options=options, providers=providers)
            self.decoder = ort.InferenceSession(self.decoder_path, sess_options=options, providers=providers)
        except Exception:
            if providers == ["CPUExecutionProvider"]:
                raise
            self.encoder = ort.InferenceSession(self.encoder_path, sess_options=options, providers=["CPUExecutionProvider"])
            self.decoder = ort.InferenceSession(self.decoder_path, sess_options=options, providers=["CPUExecutionProvider"])
        self.device = "directml" if "DmlExecutionProvider" in self.encoder.get_providers() else "cpu"

    def detect_labels(self, image_path: Path, labels: list[str]) -> list[Box]:
        return []

    @staticmethod
    def _scale(original_size: tuple[int, int]) -> float:
        return 1024.0 / max(original_size)

    def _embedding(self, image: np.ndarray) -> np.ndarray:
        height, width = image.shape[:2]
        scale = self._scale((height, width))
        resized = cv2.resize(image, (int(width * scale + 0.5), int(height * scale + 0.5)), interpolation=cv2.INTER_LINEAR)
        normalized = (resized.astype(np.float32) - np.array([123.675, 116.28, 103.53], dtype=np.float32)) / np.array([58.395, 57.12, 57.375], dtype=np.float32)
        tensor = np.zeros((1, 3, 1024, 1024), dtype=np.float32)
        tensor[0, :, : resized.shape[0], : resized.shape[1]] = normalized.transpose(2, 0, 1)
        return self.encoder.run(None, {"image": tensor})[0]

    def _predict(self, image: np.ndarray, coords: np.ndarray, labels: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        height, width = image.shape[:2]
        scale = self._scale((height, width))
        outputs = self.decoder.run(None, {
            "image_embeddings": self._embedding(image),
            "point_coords": (coords.astype(np.float32) * scale)[None, :, :],
            "point_labels": labels.astype(np.float32)[None, :],
            "mask_input": np.zeros((1, 1, 256, 256), dtype=np.float32),
            "has_mask_input": np.zeros(1, dtype=np.float32),
            "orig_im_size": np.array([height, width], dtype=np.float32),
        })
        return outputs[0][0] > 0, outputs[1][0]

    def _best_box(self, masks: np.ndarray, scores: np.ndarray, label: str, image: np.ndarray, prefer_larger: bool = False) -> list[Box]:
        if len(masks) == 0:
            return []
        areas = np.array([mask.sum() for mask in masks])
        valid = np.where(areas > 20)[0]
        if prefer_larger:
            bounded = valid[areas[valid] < image.shape[0] * image.shape[1] * 0.45]
            if len(bounded):
                valid = bounded
        if len(valid) == 0:
            return []
        if prefer_larger:
            max_score = float(scores[valid].max())
            near_best = valid[scores[valid] >= max_score - 0.12]
            best = int(near_best[np.argmax(areas[near_best])])
        else:
            best = int(valid[np.argmax(scores[valid])])
        box = mask_to_box(masks[best], label, float(scores[best])).clipped((image.shape[1], image.shape[0]))
        return [box] if box.width > 0 and box.height > 0 else []

    def detect_from_click(self, image: np.ndarray, x: int, y: int, label: str) -> list[Box]:
        masks, scores = self._predict(image, np.array([[x, y]]), np.array([1]))
        return self._best_box(masks, scores, label, image, prefer_larger=True)

    def refine_from_box(self, image: np.ndarray, query_box: tuple[int, int, int, int], label: str) -> list[Box]:
        x1, y1, x2, y2 = query_box
        masks, scores = self._predict(image, np.array([[x1, y1], [x2, y2]]), np.array([2, 3]))
        return self._best_box(masks, scores, label, image)

    def find_similar(self, image: np.ndarray, query_box: tuple[int, int, int, int], label: str) -> list[Box]:
        return ClassicalVisionBackend().find_similar(image, query_box, label)


SamClickBackend = MobileSamBackend


@dataclass
class LocateAnythingBackend:
    """Adapter for mudler/locate-anything.cpp CLI."""

    command: str
    model_path: str
    threads: int = 8
    mode: str = "hybrid"

    def detect_labels(self, image_path: Path, labels: list[str]) -> list[Box]:
        prompt = self.build_prompt(labels)
        with NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            output_path = Path(tmp.name)
        try:
            args = [
                "detect",
                "--model",
                self.model_path,
                "--input",
                str(image_path),
                "--prompt",
                prompt,
                "--output",
                str(output_path),
                "--threads",
                str(self.threads),
                "--mode",
                self.mode,
            ]
            self.run_command(args)
            return self.parse_json_boxes(output_path.read_text(encoding="utf-8"), fallback_label=labels[0] if labels else "object")
        finally:
            output_path.unlink(missing_ok=True)

    def detect_from_click(self, image: np.ndarray, x: int, y: int, label: str) -> list[Box]:
        raise RuntimeError(
            "LocateAnythingBackend is prompt-driven. Use detect_labels(image_path, labels); clicking only selects boxes."
        )

    def refine_from_box(self, image: np.ndarray, query_box: tuple[int, int, int, int], label: str) -> list[Box]:
        raise RuntimeError("LocateAnythingBackend does not support box-prompt refinement.")

    def build_prompt(self, labels: list[str]) -> str:
        cleaned = [label.strip() for label in labels if label.strip()]
        if not cleaned:
            cleaned = ["object"]
        return "Locate all the instances that matches the following description: " + "</c>".join(cleaned) + "."

    def parse_json_boxes(self, payload: str, fallback_label: str) -> list[Box]:
        data = json.loads(payload)
        boxes = data.get("detections", data.get("boxes", data if isinstance(data, list) else []))
        parsed: list[Box] = []
        for item in boxes:
            coords = item.get("box", item)
            x1, y1, x2, y2 = (int(round(float(value))) for value in coords[:4])
            parsed.append(Box(item.get("label", fallback_label), x1, y1, x2, y2, item.get("score")))
        return parsed

    def run_command(self, args: list[str]) -> str:
        completed = subprocess.run([self.command, *args], check=True, capture_output=True, text=True)
        return completed.stdout
