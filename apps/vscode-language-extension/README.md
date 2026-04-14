# vscode-language-extension

VSCode の言語拡張機能テンプレートです。シンタックスハイライトなどの言語サポートを提供する拡張機能の出発点として使用できます。

コンパイル不要のため、拡張機能フォルダ（`~/.vscode/extensions/`）に直接配置するだけで動作します。

## 構成ファイル

| ファイル | 役割 |
|---|---|
| `package.json` | 拡張機能マニフェスト（言語・文法の登録） |
| `language-configuration.json` | ブラケット・コメントなどの言語設定 |
| `syntaxes/mylang.tmLanguage.json` | TextMate 文法（シンタックスハイライト） |

## 使い方

### 1. テンプレートをコピーして名前を変更する

```
cp -r apps/vscode-language-extension ~/.vscode/extensions/mylang-0.0.1
```

> **補足**: VSCode の拡張機能フォルダのディレクトリ名は `{name}-{version}` の形式が慣例です。`package.json` の `name` と `version` に合わせて変更してください（例: `mylang-0.0.1`）。

### 2. `mylang` を実際の言語名に置き換える

以下のファイルを編集して、`mylang` / `MyLang` を実際の言語名に変更します。

- `package.json`
  - `name`, `displayName`, `description`
  - `contributes.languages[0].id`, `aliases`, `extensions`
  - `contributes.grammars[0].language`, `scopeName`, `path`
- `syntaxes/mylang.tmLanguage.json`
  - `name`, `scopeName`
  - 各パターンの `name` フィールドの `mylang` 部分
- `language-configuration.json`
  - コメント記号やブラケットを対象言語に合わせて変更

### 3. VSCode を再起動する

VSCode を再起動（または「開発者: ウィンドウの再読み込み」）すると拡張機能が有効になります。

対象の拡張子（デフォルト: `.mylang`）のファイルを開くとシンタックスハイライトが適用されます。

## 前提環境

- Visual Studio Code 1.60.0 以上
- Node.js 不要（コンパイル不要）

## カスタマイズ例

### キーワードの追加

`syntaxes/mylang.tmLanguage.json` の `keywords.patterns` にキーワードを追加します。

```json
{
  "name": "keyword.control.mylang",
  "match": "\\b(if|else|while|for|return|break|continue|your_keyword)\\b"
}
```

### 対応拡張子の追加

`package.json` の `extensions` 配列に拡張子を追加します。

```json
"extensions": [".mylang", ".ml"]
```

## 想定ユースケースと制約

- **ユースケース**: 独自 DSL や社内スクリプト言語のシンタックスハイライトを手軽に追加したい場合
- **制約**: このテンプレートはシンタックスハイライト・ブラケット補完・コメントトグルのみをサポートします。補完・定義ジャンプ・型チェックなどの高度な機能は含まれません
