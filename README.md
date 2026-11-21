## Mobile Movement Prediction

An end-to-end machine learning project for predicting human movement using mobile accelerometer data.

The project includes:

- A LightGBM activity classifier
- FastAPI-based prediction service
- MySQL dataset storage
- Docker Compose deployment
- Android sensor collection with a Rust/Python extension

## Predicted Activities

| ID | Activity |
|---:|----------|
| 0 | Downstairs |
| 1 | Jogging |
| 2 | Sitting |
| 3 | Standing |
| 4 | Upstairs |
| 5 | Walking |

## Project Structure

```text
Mobile_Moument_Prediction/
├── Mobile-side/          # Android sensor collection extension
│   ├── src/lib.rs        # Rust sensor implementation
│   ├── main.py           # Sends sensor readings to the API
│   └── pyproject.toml
├── src/
│   ├── data/             # Training and testing CSV files
│   ├── model/            # Trained model and scaler
│   ├── db_input.py       # Imports CSV data into MySQL
│   ├── train.py          # Feature engineering and model training
│   └── inferance.py      # FastAPI prediction service
├── compose.yaml
├── Containerfile
└── pyproject.toml
```

## Dataset

The repository contains training and testing accelerometer data.

Each data record should include:

- `timestamp`
- `acc_x`
- `acc_y`
- `acc_z`
- `Activity` — used during training

The activity distribution and preprocessing requirements are documented in [`src/data/data_info.txt`](./src/data/data_info.txt).

## Features

During preprocessing, the project creates:

- Magnitude of gravity (`mgs`)
- Sum of absolute acceleration values (`sma`)
- Rolling means and standard deviations
- Rolling minimum and maximum values
- Rolling correlations between accelerometer axes

The processed features are standardized and used to train a balanced LightGBM classifier.

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- Docker and Docker Compose
- An Android device for mobile sensor collection
- Rust and Python Android toolchains for building the mobile extension

## Environment Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Configure the database credentials:

```env
DB_HOST=db
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=your_database
```

## Run with Docker Compose

Build and start the API and MySQL database:

```bash
docker compose up --build
``>

The API is exposed at:

```text
http://localhost:8000
``>

Interactive API documentation is available at:

```text
http://localhost:8000/docs
``>

## Run Locally

Install dependencies:

```bash
uv sync
```

Train the model:

```bash
uv run src/train.py
```

Start the prediction service:

```bash
uv run uvicorn src.inferance:app --host 0.0.0.0 --port 8000
```

## Prediction API

Send accelerometer readings to the `/infer/` endpoint:

```bash
curl -X POST "http://localhost:8000/infer/" \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      [0.0, 1.2, -0.3, 9.8],
      [1.0, 1.1, -0.2, 9.7]
    ]
  }'
```

The input format is:

```text
[timestamp, acc_x, acc_y, acc_z]
```

Example response:

```json
{
  "value": 5,
  "prediction": "Walking"
}
```

## Android Sensor Collection

The Rust-based sensor extension can collect accelerometer events on Android.

After building and installing the extension on Termux run:

```bash
cd Mobile-side
uv add requests
uv sync
```

Update `Mobile-side/main.py` with the server IP address:

```python
url = "http://YOUR_PC_IP:8000/infer/"
```

Then run the sensor client:

```bash
uv run main.py
```

If you Fase Some Issue With uv build. One Can Alternatively, build a wheel manually and run the Python environment directly

```bash
pkg install maturin
uv venv                 # only if .venv doesn't already exist
source script.sh
maturin build --release
uv pip intall requests
uv pip install --python-platform aarch64-linux-android target/wheels/*.whl
.venv/bin/python main.py
```

## License

This project is available under the [MIT License](./LICENSE).

## Project Status

This repository is an active prototype. Before deploying or retraining in a new environment, review the database setup and model/data paths in `src/train.py`, `src/db_input.py`, and `src/inferance.py`.

