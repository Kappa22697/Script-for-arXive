# paper_translator.py
import argparse
import requests
import json
import arxiv
import re
import time
import textwrap

# Ollama APIのエンドポイントと使用するモデル
OLLAMA_API_URL = "http://localhost:11434/api/generate"

def sanitize_filename(filename: str) -> str:
    """ファイル名として使えない文字をアンダースコアに置換する"""
    return re.sub(r'[\\/:*?"<>|]', '_', filename)

def translate_text_with_ollama(text: str, model_name: str) -> str:
    """
    Ollama APIを使用して、指定されたテキストを日本語に翻訳します。

    Args:
        text: 翻訳する英語のテキスト。

    Returns:
        翻訳された日本語のテキスト。エラーが発生した場合はエラーメッセージを返します。
    """
    # プロンプトをさらに厳格化し、ローマ字出力や不完全な翻訳を防ぐ
    prompt = f"""You are a silent, professional Japanese translation engine. Your task is to translate the following English academic abstract into Japanese.

**Strict Instructions:**
- **CRITICAL: You MUST output using Japanese characters (Kanji, Hiragana, Katakana). Do NOT use Romaji.**
- Translate the text into natural-sounding, clear, and accurate Japanese.
- Maintain a professional and academic tone.
- **CRITICAL: You MUST complete the translation.** Do not stop halfway.
- **CRITICAL: Do NOT output ANYTHING other than the translated Japanese text.** Do not include preambles, apologies, or any meta-commentary.

--- English Abstract ---
{text}
--- End of Abstract ---
"""
    
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False  # ストリーミングなしで一度にレスポンスを受け取る
    }
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=180)
        response.raise_for_status()
        # 文字化け対策：レスポンスを明示的にutf-8でデコードしてからJSONとして解析する
        # エラーが発生しても無視して、デコード可能な部分だけを処理する
        response_text = response.content.decode('utf-8', errors='ignore')
        response_data = json.loads(response_text)
        translated_text = response_data.get("response", "翻訳結果がありません。").strip()

        # 翻訳結果から典型的な不要部分を削除する後処理
        unwanted_phrases = ["Here is the translation:", "Here is the translation of the English text into Japanese:"]
        for phrase in unwanted_phrases:
            translated_text = translated_text.replace(phrase, "")

        return translated_text

    except requests.exceptions.RequestException as e:
        print(f"Ollama APIへの接続中にエラーが発生しました: {e}")
        return "翻訳エラー：Ollama APIに接続できませんでした。Ollamaが起動しているか確認してください。"
    except json.JSONDecodeError:
        return "翻訳エラー：Ollamaからのレスポンスの解析に失敗しました。"

def is_translation_error(translated_text: str) -> bool:
    """
    翻訳結果がエラーメッセージかどうかを判定します。
    """
    return translated_text.startswith("翻訳エラー")


def search_and_translate_papers(query: str, max_results: int, model_name: str):
    """
    arXivで論文を検索し、その要旨を日本語に翻訳します。

    Args:
        query: 検索キーワード。
        max_results: 取得する論文の最大数。
        model_name: 翻訳に使用するOllamaモデル名。
    """
    # 検索クエリをファイル名として使えるように整形
    base_filename = query.replace(" ", "_").lower()
    filename = sanitize_filename(base_filename) + "_results.txt"
    print(f"'{query}'に関する論文をarXivで検索しています...")
    
    try:
        # DeprecationWarningを解消するため、推奨されるClientを使用する
        client = arxiv.Client()
        search = client.results(arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        ))
        results = list(search)

        if not results:
            print("関連する論文が見つかりませんでした。")
            return

        print(f"{len(results)}件の論文が見つかりました。")
        print("-" * 50)

        # 結果を書き込むファイルを開く (UTF-8エンコーディングを指定)
        with open(filename, "w", encoding="utf-8") as f:
            for i, result in enumerate(results):
                print(f"[{i+1}/{len(results)}] 処理中: {result.title}")
                print("  要旨を翻訳しています...", end="", flush=True)
                
                # 要旨を翻訳
                abstract = result.summary.replace('\n', ' ')
                translated_abstract = translate_text_with_ollama(abstract, model_name=model_name)
                
                if is_translation_error(translated_abstract):
                    print(f" 失敗しました。エラー: {translated_abstract}")
                else:
                    print(" 完了しました。")

                # 読みやすさのために、翻訳された要旨を50文字で改行する
                formatted_abstract = textwrap.fill(translated_abstract, width=50)

                # ファイルに書き込む内容を組み立てる
                output_content = (
                    f"■ タイトル: {result.title}\n"
                    f"■ URL: {result.entry_id}\n\n"
                    f"--- 翻訳された要旨 ---\n"
                    f"{formatted_abstract}\n"
                    f"{'-'*50}\n\n"
                )
                
                # ファイルに書き込む
                f.write(output_content)

                # 最後の論文でなければ、APIへの負荷を考慮して少し待機する
                if i < len(results) - 1:
                    time.sleep(1) # 1秒待機

        
        print(f"\n処理が完了しました。結果は '{filename}' に保存されました。")

    except Exception as e:
        print(f"論文の検索または処理中にエラーが発生しました: {e}")


def main():
    """
    メイン関数。コマンドライン引数を解析し、論文検索と翻訳を実行します。
    """
    parser = argparse.ArgumentParser(
        description="arXivで論文を検索し、Ollamaを使って要旨を日本語に翻訳します。複数のキーワードを指定すると、それら全ての共通部分(AND検索)を検索します。"
    )
    parser.add_argument(
        "queries", 
        type=str, 
        nargs='+',  # 1つ以上の引数を受け取る
        help="検索したい論文のキーワード。スペースを含む場合は \"\" で囲んでください。複数指定するとAND検索になります。(例: \"transformer\" \"quantum\")"
    )
    parser.add_argument("--max", type=int, default=3, help="検索する論文の最大数")
    parser.add_argument("--model", type=str, default="llama3", help="翻訳に使用するOllamaモデル名 (例: phi3:medium)")
    
    args = parser.parse_args()
    
    # 複数のキーワードを " AND " で連結してAND検索クエリを作成
    # 各キーワードは括弧で囲み、検索の優先順位と正確性を担保する
    combined_query = " AND ".join(f"({q})" for q in args.queries)
    model_to_use = args.model
    
    print(f"\n{'='*20} 共通クエリ: '{combined_query}' の処理を開始 {'='*20}")
    search_and_translate_papers(query=combined_query, max_results=args.max, model_name=model_to_use)
    print(f"\n{'='*20} 処理が完了しました {'='*20}")


if __name__ == "__main__":
    main()
