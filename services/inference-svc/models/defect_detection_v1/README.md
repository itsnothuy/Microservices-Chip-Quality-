# Defect Detection Model v1

This directory contains the defect detection model for PCB and semiconductor inspection.

## Model Information

- **Model Name**: defect_detection_v1
- **Version**: 1
- **Platform**: ONNX Runtime
- **Input**: RGB images (1024x1024)
- **Output**: Defect predictions with bounding boxes and classifications

## Configuration

See `config.pbtxt` for Triton model configuration.

## Performance

- Inference Latency: ~45ms per image
- Throughput: ~120 images/second with batching
- GPU Memory: ~2GB

## Training Details

- Dataset: 50,000 annotated PCB images
- Architecture: YOLO-based object detection
- Accuracy: 95.3% on validation set
- Classes: 10 defect types (scratch, void, contamination, etc.)

## Usage

Load model via inference service API:
```bash
POST /api/v1/models/deploy
{
  "model_name": "defect_detection_v1",
  "version": "1",
  "set_as_default": true
}
```
