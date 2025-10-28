# Script-for-arXive

Ollamaを使用してarXivから論文を検索し、要旨を日本語に翻訳するPythonスクリプトです。

## 機能

- arXivから論文を検索（AND検索対応）
- Ollama APIを使用した論文要旨の日本語翻訳
- 翻訳結果をテキストファイルに保存
- 複数のキーワードによる詳細検索

## 必要な環境

### 開発環境

- OS: Kubuntu 24.04
- CPU: Intel i7-14700KF (28) @ 5.500GHz
- GPU: NVIDIA GeForce RTX (CUDA対応)

### 依存パッケージ

```bash
pip install arxiv requests
```

### Ollama

- Ollamaがローカル環境で起動している必要があります
- デフォルトエンドポイント: `http://localhost:11434/api/generate`
- デフォルトモデル: `llama3`

## 使い方

### 基本的な使用例

```bash
python test1.py "transformer"
```

### 複数キーワードでAND検索

```bash
python test1.py "transformer" "quantum"
```

### オプション指定

```bash
python test1.py "machine learning" --max 5 --model phi3:medium
```

## コマンドライン引数

| 引数 | 必須/オプション | 説明 | デフォルト値 |
|------|----------------|------|-------------|
| `queries` | 必須 | 検索キーワード（複数指定可）。スペースを含む場合は`""`で囲む | - |
| `--max` | オプション | 検索する論文の最大数 | 3 |
| `--model` | オプション | 使用するOllamaモデル名 | llama3 |

## 出力ファイル

実行すると、検索クエリに基づいた名前のテキストファイルが生成されます。

例: `transformer_results.txt`

### 出力フォーマット

```
■ タイトル: 論文タイトル
■ URL: https://arxiv.org/abs/xxxx.xxxxx

--- 翻訳された要旨 ---
翻訳された日本語の要旨がここに表示されます。
--------------------------------------------------
```

## 主な関数

### `translate_text_with_ollama(text: str, model_name: str) -> str`

Ollama APIを使用してテキストを日本語に翻訳します。

- **引数**
  - `text`: 翻訳する英語のテキスト
  - `model_name`: 使用するOllamaモデル名
- **戻り値**: 翻訳された日本語テキスト

### `search_and_translate_papers(query: str, max_results: int, model_name: str)`

arXivで論文を検索し、要旨を翻訳してファイルに保存します。

- **引数**
  - `query`: 検索クエリ
  - `max_results`: 取得する論文の最大数
  - `model_name`: 使用するOllamaモデル名

### `sanitize_filename(filename: str) -> str`

ファイル名として使用できない文字をアンダースコアに置換します。

## エラー処理

- Ollama APIへの接続エラー
- JSON解析エラー
- 翻訳エラー（エラーメッセージが返される場合）

エラーが発生した場合は、該当する論文の処理をスキップして次に進みます。

## 注意事項

- APIへの負荷を考慮し、各論文の処理後に1秒間の待機時間を設けています
- 翻訳タイムアウトは180秒に設定されています
- 出力ファイルはUTF-8エンコーディングで保存されます
- 翻訳結果は50文字で自動的に改行されます

## トラブルシューティング

### Ollamaに接続できない

```
翻訳エラー：Ollama APIに接続できませんでした。
```

→ Ollamaが起動しているか確認してください

```bash
ollama serve
```

### 指定したモデルが見つからない

→ 使用可能なモデルを確認してください

```bash
ollama list
```

必要に応じてモデルをダウンロードしてください

```bash
ollama pull llama3
```

## ライセンス

このスクリプトは個人利用および学術研究目的で自由に使用できます。
