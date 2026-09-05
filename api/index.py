"""Ponto de entrada para deploy serverless na Vercel.

A Vercel (builder @vercel/python) detecta automaticamente uma aplicacao ASGI
exportada como `app` neste arquivo e a serve como funcao serverless.
Toda a logica real da aplicacao continua em app/ (nao duplicar aqui).
"""

from app.main import app  # noqa: F401
