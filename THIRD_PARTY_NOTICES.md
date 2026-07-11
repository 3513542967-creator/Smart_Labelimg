# Third-Party Notices

Smart_labelimg is distributed under the MIT License. The following independent
projects and runtime components retain their own copyrights and licenses.

## LabelImg

- Project: https://github.com/HumanSignal/labelImg
- License: MIT License
- Use in this project: workflow inspiration and interoperability with common
  YOLO TXT and Pascal VOC XML annotation conventions.
- Smart_labelimg does not claim to be an official LabelImg distribution.

## MobileSAM

- Project: https://github.com/ChaoningZhang/MobileSAM
- License: Apache License 2.0
- Use in this project: MobileSAM model architecture and weights, converted into
  ONNX image-encoder and prompt-decoder artifacts for local inference.
- The conversion and Windows integration are modifications made by this project.

## Runtime components

The Windows distribution also contains or depends on open-source components,
including Python, PySide6/Qt, NumPy, OpenCV, Pillow, ONNX Runtime DirectML,
PyInstaller, and their transitive dependencies. Their licenses are provided by
their respective projects and are not replaced by the Smart_labelimg license.

## Formats and trademarks

YOLO TXT and Pascal VOC XML are supported for dataset interoperability. Product
and project names are used only to identify compatibility or upstream origin.
No endorsement by upstream authors, Microsoft, GPU vendors, or other third
parties is implied.
