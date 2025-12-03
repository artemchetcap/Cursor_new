from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "users" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL /* Internal identifier */,
    "telegram_id" BIGINT NOT NULL UNIQUE /* Unique ID in Telegram */,
    "username" VARCHAR(255) /* Username (@username) */,
    "full_name" VARCHAR(255) /* Full name */,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP /* Registration date */
) /* Model representing a Telegram user. */;
CREATE INDEX IF NOT EXISTS "idx_users_telegra_ab91e9" ON "users" ("telegram_id");
CREATE TABLE IF NOT EXISTS "summary_requests" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL /* Unique request number */,
    "content_type" VARCHAR(50) NOT NULL /* Content type (youtube, article, text, file) */,
    "source_url" TEXT /* Source link (or null for text) */,
    "status" VARCHAR(50) NOT NULL DEFAULT 'processing' /* Result (success, error, processing) */,
    "tokens_used" INT NOT NULL DEFAULT 0 /* Number of tokens used (cost) */,
    "error_message" TEXT /* Error text (if status is error) */,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP /* Request time */,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE /* Reference to user */
) /* Model representing a summary request (Analytics). */;
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "eJzlmW1z2jgQgP+Khk90hstQEpLcfTpCSMu1gRsgd512Oh5hC6PBlqgkN2E6/PdbyTbGr4"
    "U0JfTyzWhfvHq0lnbFt5rPHeLJk3Hg+1isRuRLQKSq/YG+1Rj2CTyUaDRQDS+XiVwPKDz1"
    "jIkMdS0RKhshnkolsK19z7AnCQw5RNqCLhXlTFvdakdIkKUgkjBFmYswilyhyBWqdxj2Vo"
    "ra8tWJdutwG/yC7qM9BIyCwFLcJWpOBPj59BmGKXPIA5Hxz+XCmlHiOSk01NEOzLilVksz"
    "1mfqxijq4KaWzb3AZ4nycqXmnG20KTMoXcKIwIpo90oEGg4LPC/iGfMKI01UwhC3bBwyw4"
    "GnEWvrPOE742BDggX+FCacoRiZ2pzpBYMApZmzq1/8W+v12cXZ5en52SWomOA2IxfrcMYJ"
    "jtDQQBlMamsjxwqHGoZsghJep2DJQjA5qN05FsVUs3YZvjCFLN+YZhXgeCAhnORsNeJuGA"
    "/SAaD6igcqmIIdFpBwHjwo8qAaaEY98mpH8D5+sDzCXDWHn+1mBeV/OqPu286o3m4a3xw+"
    "t/B7HESSlhHphUjASx4Im1iB8PLYJxBsMfa01aOgRzn7BMzHJhjkUbZAdS6MFprBg4a9I+"
    "YKrJPeh4l24kv5xdvGWb/tfDDu/VUkeT8cvInVt/B33w+vstgVVoHcJ9MTi8PleG0puE2k"
    "1OTy3EdEghqqy8DWSg1EhOCigRKjI8lxxReESSuQZJ8NO2P1/Z37qag386gHZqtGfIbCqJ"
    "COCtVtLndN8KfZwBOmZq0tH9YZuwU7dvnWkTN85t2jp+MxWwWq0xkKPzNEZZjNR7p92IJo"
    "NhZWefTXIFHUJyUHZsoyw96JTE/ih8MenlFxieI375DVMBtnyLxVlBJV69C/7Y0nndu/U4"
    "tx3Zn0tKSVWoh4tH6e2WU2TtC//clbpH+ij8NBz7CEj9EV5o2J3uRjTceEA8Utxu8t7GzV"
    "a/FojCi1xPCFC2uvCnPL4nCbVdlKzoggDE5lxfVedcAqU1frs0VhkRkHkuZ5wwWhLntHVg"
    "ZrHyLCEHkBxqgVuovcHD3OdZwh8WiSegLfbxqa7cSB2cIciQqLkc6427nu1QzTKbYX91g4"
    "VgqulvAWz4xsdPMiv+VnRzCDk8CJZqFj3uZc0IrG/MsbUD2hH+k6J4DAFdg3rHfsM/M2L6"
    "izhNiIgL4aUUcDgcCPpK9U0aoU7qRX1C2v/tKGT7Oh/mDj3r9GlG0SbS/Av7dap6cXrebp"
    "+WX77OKifdnckM6LqpBf9d9o6qlTMV8d6m/APO/R4GzbPHNNeBeFgup/xlE9qpVptds79D"
    "KgVdrMGFma7QxebO0LN2X0zHRvdH8ex3IUSP+v5bRLNUj9G+kQXmRNnasHy4uZJCG2b64z"
    "Z0ZkefNuRDyDtrxQzN+Z/7Il4/pnFnodIqg9Lyr1IkllsYcTne9VezGqPIaXU6uVMzhwaf"
    "YVavTo89n1FNsyeeaL/t0p/vzTS38ae0CM1H9NgK+bu9wOg1YpQCPLHP/hnzZ5iH+Nh4PK"
    "/50KQEKtztknh9qqgTw4fz8fJ9YKinrW1TeW2cvJzEmtHVwVXcUc8h5h/R8na+vW"
)
