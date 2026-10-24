# MiniMart Cart API

Backend de protótipo para catálogo, estoque reservado em carrinhos, cupons e checkout. Os dados permanecem no SQLite do projeto, que já vem com o catálogo e os cupons promocionais iniciais.

O banco `src/database/database.db` já inclui o catálogo inicial:

| Produto | Preço | Estoque |
| --- | ---: | ---: |
| Mouse sem fio | R$ 79,90 | 5 |
| Teclado mecânico | R$ 249,90 | 2 |
| Fone de ouvido bluetooth | R$ 159,90 | 3 |
| Webcam Full HD | R$ 199,90 | 1 |
| Carregador USB-C | R$ 119,90 | 3 |

Também estão cadastrados os cupons `OFERTA5` (5%) e `PROMO10` (10%). Os pagamentos aceitos no checkout são `pix` e `credit_card`.

## Executar

```powershell
uv run uvicorn src.main:app --reload
```

Documentação interativa: `http://127.0.0.1:8000/docs`.

## Fluxo da API

1. Consulte o catálogo inicial em `GET /api/v1/products/`; novos produtos podem ser cadastrados em `POST /api/v1/products/`, com `name`, `price` e `amount`.
2. Os cupons `OFERTA5` e `PROMO10` já estão disponíveis. Cupons adicionais podem ser cadastrados em `POST /api/v1/coupons/`, com `code` e `discount` entre `0` e `1` (por exemplo, `0.10` para 10%).
3. Crie um carrinho em `POST /api/v1/carts/`.
4. Reserve unidades em `POST /api/v1/carts/{cart_id}/items`. O estoque disponível diminui na reserva.
5. Consulte o carrinho em `GET /api/v1/carts/{cart_id}`; atualize quantidades com `PUT /api/v1/carts/{cart_id}/items/{product_id}` ou devolva o estoque com `DELETE` nessa rota.
6. Finalize em `POST /api/v1/carts/{cart_id}/checkout?payment_method=pix&coupon_code=PROMO10`. O cupom é opcional; use `credit_card` para pagamento sem desconto adicional.

Uma reserva acima do estoque disponível é rejeitada sem alterar estoque nem carrinho. Remover um item ou excluir o carrinho libera as unidades reservadas. O checkout mantém a baixa de estoque, aplica primeiro o cupom e depois o desconto do Pix, apresenta os valores por item e limpa os itens e o cupom do carrinho.

## Testes

```powershell
uv run pytest
```
