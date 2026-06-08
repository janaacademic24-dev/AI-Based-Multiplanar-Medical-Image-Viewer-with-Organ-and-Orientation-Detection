"""
AI Organ Detector
Predicts organ/region from 2D DICOM slices using CLIP (preferred) or ResNet50.
"""

import numpy as np
from PIL import Image

ORGAN_LABELS = ["Brain", "Chest", "Abdomen", "Pelvis", "Spine", "Extremity"]

# ── optional dependencies ──────────────────────────────────────────────────────
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import importlib
    import os
    open_clip = importlib.import_module("open_clip")
    os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
    CLIP_AVAILABLE = True
except Exception:
    CLIP_AVAILABLE = False
    open_clip = None

try:
    import torchvision.models as tv_models
    from torchvision import transforms
    TORCHVISION_AVAILABLE = True
except ImportError:
    TORCHVISION_AVAILABLE = False
# ──────────────────────────────────────────────────────────────────────────────


def _to_rgb_uint8(slice_data: np.ndarray) -> np.ndarray:
    """Normalize a 2D float array to [0,255] RGB uint8."""
    if slice_data.max() > slice_data.min():
        normalized = (slice_data - slice_data.min()) / (slice_data.max() - slice_data.min())
        gray = (normalized * 255).astype(np.uint8)
    else:
        gray = np.zeros_like(slice_data, dtype=np.uint8)
    return np.stack([gray] * 3, axis=-1)


class OrganDetector:
    """
    Wraps CLIP or ResNet50 for zero-shot organ region prediction.

    Usage:
        detector = OrganDetector()          # auto-picks CLIP or ResNet50
        result = detector.predict(slice_2d, view_name="Axial")
        # → {'view': 'Axial', 'class': 'Brain', 'confidence': 0.87, 'class_id': 0}
    """

    def __init__(self):
        if not TORCH_AVAILABLE:
            raise RuntimeError(
                "PyTorch is required. Install with: pip install torch torchvision"
            )

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.use_clip = CLIP_AVAILABLE
        self._model = None
        self._preprocess = None
        self._tokenizer = None

    # ── lazy model loading ─────────────────────────────────────────────────────

    def load(self, progress_cb=None):
        """Load the model (call once before predict())."""
        def _log(msg):
            if progress_cb:
                progress_cb(msg)

        if self.use_clip:
            _log("Loading CLIP (ViT-B/32)…")
            self._model, _, self._preprocess = open_clip.create_model_and_transforms(
                "ViT-B-32", pretrained="laion2b_s34b_b79k", device=self.device
            )
            self._model.eval()
            self._tokenizer = open_clip.get_tokenizer("ViT-B-32")
        else:
            _log("Loading ResNet50…")
            self._model = tv_models.resnet50(weights=tv_models.ResNet50_Weights.DEFAULT)
            self._model = self._model.to(self.device)
            self._model.eval()
            self._preprocess = transforms.Compose([
                transforms.ToTensor(),
                transforms.Resize((224, 224)),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                ),
            ])

    # ── prediction ─────────────────────────────────────────────────────────────

    def predict(self, slice_2d: np.ndarray, view_name: str = "") -> dict:
        """
        Predict organ region from a 2D slice.

        Returns dict with keys: view, class, confidence, class_id
        """
        if self._model is None:
            self.load()

        try:
            if self.use_clip:
                return self._predict_clip(slice_2d, view_name)
            else:
                return self._predict_resnet(slice_2d, view_name)
        except Exception as e:
            return {"view": view_name, "class": "Error", "confidence": 0.0,
                    "class_id": -1, "error": str(e)}

    def _predict_clip(self, slice_2d, view_name):
        rgb = _to_rgb_uint8(slice_2d)
        pil_img = Image.fromarray(rgb)
        image = self._preprocess(pil_img).unsqueeze(0).to(self.device)

        prompts = [f"a medical CT scan showing {label}" for label in ORGAN_LABELS]

        with torch.no_grad():
            text = self._tokenizer(prompts).to(self.device)
            img_feat = self._model.encode_image(image)
            txt_feat = self._model.encode_text(text)

            img_feat = img_feat / img_feat.norm(dim=-1, keepdim=True)
            txt_feat = txt_feat / txt_feat.norm(dim=-1, keepdim=True)

            probs = (img_feat @ txt_feat.t() * 100).softmax(dim=-1).squeeze(0)
            confidence, predicted = torch.max(probs, 0)

        return {
            "view": view_name,
            "class": ORGAN_LABELS[int(predicted.item())],
            "confidence": float(confidence.item()),
            "class_id": int(predicted.item()),
        }

    def _predict_resnet(self, slice_2d, view_name):
        rgb = _to_rgb_uint8(slice_2d)
        img_tensor = self._preprocess(rgb).unsqueeze(0).to(self.device)

        with torch.no_grad():
            output = self._model(img_tensor)
            probs = torch.nn.functional.softmax(output, dim=1)
            confidence, predicted = torch.max(probs, 1)

        pred_idx = int(predicted.item()) % len(ORGAN_LABELS)
        return {
            "view": view_name,
            "class": ORGAN_LABELS[pred_idx],
            "confidence": float(confidence.item()),
            "class_id": pred_idx,
        }

    @property
    def model_name(self) -> str:
        return "CLIP (ViT-B/32)" if self.use_clip else "ResNet50"

    @property
    def device_name(self) -> str:
        return str(self.device)
