# **OIKIA_SV**

API for the OIKIA application, which simplifies the discovery of the ideal place to live.

## Tests


## Déploiement

[![Deploy API Demo EC2](https://github.com/raizestudio/heracles/actions/workflows/deploy.yml/badge.svg)](https://github.com/raizestudio/heracles/actions/workflows/deploy.yml)
![Deploy Client Vercel](https://deploy-badge.vercel.app/vercel/heracles-six)

## Installation

### Backend

```bash
# Clone the repository
git clone https://github.com/raizestudio/heracles.git

# Navigate to the project directory
cd heracles

# Create venv
python3.13 -m venv venv

# Activate venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Create .env file
touch .env

# or copy .env.example
cp .env.example .env

# Start API
uvicorn main:app --reload
```

### Frontend

```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm i --force

# Start App
npm run dev
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