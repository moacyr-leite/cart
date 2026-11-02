# MiniMart Cart API

Backend de protótipo para catálogo, estoque reservado em carrinhos, cupons e checkout. O banco
de dados roda em PostgreSQL via Docker Compose, é criado por migrações do Alembic e populado por
um script de seed.

O seed inclui o catálogo inicial:

| Produto | Preço | Estoque |
| --- | ---: | ---: |
| Mouse sem fio | R$ 79,90 | 5 |
| Teclado mecânico | R$ 249,90 | 2 |
| Fone de ouvido bluetooth | R$ 159,90 | 3 |
| Webcam Full HD | R$ 199,90 | 1 |
| Carregador USB-C | R$ 119,90 | 3 |

Também estão cadastrados os cupons `OFERTA5` (5%) e `PROMO10` (10%). Os pagamentos aceitos no
checkout são `pix` e `credit_card`.

## Requisitos

- Python 3.10+ (o projeto usa 3.14 no `.python-version`)
- [uv](https://docs.astral.sh/uv/)
- Docker com Docker Compose

## Banco de dados

Suba o PostgreSQL e prepare o ambiente:

```powershell
Copy-Item .env.example .env
docker compose up -d --wait db
uv sync
uv run alembic upgrade head
uv run python -m src.database.seed
```

As credenciais padrão do Compose são `cart`/`cart` no banco `cart`. Se alterar
`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` ou `POSTGRES_PORT`, mantenha a
`DATABASE_URL` do `.env` em sincronia.

Para parar o banco:

```powershell
docker compose down
```

Para remover também os dados persistidos no volume:

```powershell
docker compose down -v
```

## Executar

```powershell
uv run uvicorn src.main:app --reload
```

A URL do banco é definida por `DATABASE_URL` (veja `.env.example`). O valor padrão aponta para o
container local em `localhost:5432`.

Documentação interativa: `http://127.0.0.1:8000/docs`. Health check: `GET /health`.

### Migrações

```powershell
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "descricao"
```

## Fluxo da API

1. Consulte o catálogo inicial em `GET /api/v1/products/`; novos produtos podem ser cadastrados em `POST /api/v1/products/`, com `name`, `price` e `amount`. O nome é único sem diferenciar maiúsculas/minúsculas.
2. Os cupons `OFERTA5` e `PROMO10` já estão disponíveis. Cupons adicionais podem ser cadastrados em `POST /api/v1/coupons/`, com `code` e `discount` entre `0` e `1` (por exemplo, `0.10` para 10%).
3. Crie um carrinho em `POST /api/v1/carts/`; o `id` é gerado pelo servidor.
4. Reserve unidades em `POST /api/v1/carts/{cart_id}/items`. O estoque disponível diminui na reserva.
5. Consulte o carrinho em `GET /api/v1/carts/{cart_id}`; atualize quantidades com `PUT /api/v1/carts/{cart_id}/items/{product_id}` ou devolva o estoque com `DELETE` nessa rota.
6. Finalize em `POST /api/v1/carts/{cart_id}/checkout?payment_method=pix&coupon_code=PROMO10`. O cupom é opcional; use `credit_card` para pagamento sem desconto adicional.
7. O checkout gera um pedido persistido com `status=paid` e `payment_status=approved`, e retorna `order_id`. Consulte-o em `GET /api/v1/orders/{order_id}`.
8. Cancele um pedido pago em `POST /api/v1/orders/{order_id}/cancel`. O status passa para `cancelled`, o pagamento para `refunded` e as unidades voltam ao estoque. Cancelar novamente é idempotente.

O checkout aceita o header `Idempotency-Key` (1–255 caracteres: letras, números, `-`, `_`, `.` e
`:`). Repetir a mesma chave com o mesmo carrinho e o mesmo payload devolve o mesmo pedido;
reutilizá-la em outro carrinho ou com `payment_method`/`coupon_code` diferentes retorna `409`.
Chaves fora do formato retornam `422`.

Uma reserva acima do estoque disponível é rejeitada sem alterar estoque nem carrinho. Remover um
item ou excluir o carrinho libera as unidades reservadas. O checkout mantém a baixa de estoque,
aplica primeiro o cupom e depois o desconto do Pix, apresenta os valores por item, registra o
pedido e limpa os itens e o cupom do carrinho.

## Qualidade e testes

```powershell
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
```

O `pytest` executa a suíte com cobertura de `src` via `pytest-cov`. Os testes padrão usam um banco
SQLite temporário por teste, sessões independentes por requisição e validam que o banco começa
vazio. O CI exige cobertura mínima de 90% no job de testes unitários.

Os testes de integração usam PostgreSQL. Com o container rodando e as migrações aplicadas:

```powershell
$env:TEST_DATABASE_URL = "postgresql+psycopg://cart:cart@localhost:5432/cart"
uv run alembic upgrade head
uv run pytest --no-cov
```

O workflow em `.github/workflows/ci.yml` executa lint, formatação e tipagem em pushes para a
`main` e pull requests. Os testes unitários com cobertura rodam em pushes para a `main` e pull
requests; os testes de integração com PostgreSQL rodam em cada push para a `main`.
