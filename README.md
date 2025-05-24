# **OIKIA_SV**

API for the OIKIA application, which simplifies the discovery of the ideal place to live.

## Tests


## Déploiement

[![API Tests](https://github.com/raizestudio/oikia_sv/actions/workflows/api_tests.yml/badge.svg)](https://github.com/raizestudio/oikia_sv/actions/workflows/api_tests.yml)
[![codecov](https://codecov.io/gh/raizestudio/oikia_sv/graph/badge.svg?token=K2RMUK0Z48)](https://codecov.io/gh/raizestudio/oikia_sv)

## Installation

# TODO:

### Backend

```bash
# Clone the repository
git clone https://github.com/raizestudio/oikia_sv.git

# Navigate to the project directory
cd oikia_sv

# Create venv
python3.13 -m venv venv

# Activate venv
source venv/bin/activate

# Install requirements
uv pip install -r pyproject.toml

# or simply 
make init

# Create .env file
touch .env

# or copy .env.example
cp .env.example .env

# Start API
uvicorn main:app --reload

```	

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/fooBar`)
3. Commit your changes (`git commit -m 'Add some fooBar'`)
4. Push to the branch (`git push origin feature/fooBar`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Contact

Joel P. - [raizetvision@gmail.com](mailto:raizetvision@gmail.com)

Project Link: [https://github.com/raizestudio/heracles](https://github.com/raizestudio/heracles)