# Main Source for BFD9020

The main entrypoint for this project is `main.py`, if run directly, it will start a
uvicorn server on port 9020.

## Layout

```
main.py                                # Main webserver
config.py                              # Main settings for the entire project
classifier.py                          # Python bindings for our classifiers
onnx_wrapper.py                        # ONNX runtime wrapper using our classifier definitions
model_manager.py                       # Model manager to retrieving, accessing, or checking on loaded models
image_utils.py                         # Basic image manipulation tools for user-sent files
models/
  xtype-simple_resnet18_fp16_01        # X-ray type classifier
  lateral_fliprot_resnet18_fp16_07     # Lateral ceph flip/rotation classifier
  frontal_fliprot_resnet18_fp16_03     # Frontal ceph flip/rotation classifier
static/
  BFD9020.html                         # Browser endpoint tester (also served at /test)
typings/                               # Some manual typings for the skimage package, not required in production
```

## Models

Three ONNX exported learners are loaded at startup:

| Key       | Path                                      | Purpose                                  |
| --------- | ----------------------------------------- | ---------------------------------------- |
| `xray`    | `models/xtype-simple_resnet18_fp16_01`    | Coarse X-ray type classification         |
| `lateral` | `models/lateral_fliprot_resnet18_fp16_07` | Flip/rotation inference for lateral ceph |
| `frontal` | `models/frontal_fliprot_resnet18_fp16_03` | Flip/rotation inference for frontal ceph |

All three are ResNet-18 models trained with FP16 and exported via `fastai`'s `export()`
and converted with the provided converter script at `/converter` They are committed as
binary blobs (not Python packages).

## Linting & Formatting

Basedpyright and Ruff are the enforced checker/linter/formatters for this repository for
python files. During a PR, these will be checked in a CI job.

To run the repo-wide formatter, run `nix fmt` from the repo root. We would recommend
getting the basedpyright and ruff extensions for your editor to get warnings and errors
during development.

You may run the full repo checks by running `nix flake check` at any time. Mypy is not
enforced on this repo.

### FastAPI conventions

- All FastAPI functions should have an explicit return type AND an explict
  `response_model`, these will most likely be the same type.
- All file parameters should be annotated as such: `Annotated[UploadFile, File()]`
- All endpoints should be async
- Use `Result` when possible, but unwrap into an `HTTPException` in an endpoint response
  function.
