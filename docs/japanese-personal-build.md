# 個人用の日本語ビルド

この作業ブランチは、NectarLink **v0.1.5**
（`58e530f27726aee19a66746576b0e6c764d4278d`）の日本語化です。
公式リリースではありません。翻訳は機械翻訳の下書きを基に、主要なUI用語・
権限の案内・埋め込み変数を調整しています。実機での表示確認は別途必要です。

## 変更した内容

- AndroidとWindowsの画面、設定、通知、機能ガイドを日本語化。
- 言語選択に「日本語」を追加。日本語のOSではシステム設定に追従。
- Androidの日本語地域コード（`ja-JP`など）と複数形を処理。
- `scripts/check-japanese.py`で全翻訳の収録範囲と埋め込み変数を検証。
- AndroidはリポジトリのActions Secretsに保存した鍵で署名。
  最初に渡したAPKと同じ証明書であることをビルド時に検証。

機能やネットワーク接続方式は、本家v0.1.5のままです。
日本語化によって未実装の機能が増えるわけではありません。

## ビルド

GitHub Actionsの **Japanese personal build** を使用します。
`ja-v0.1.5`へのpushまたは手動実行で、次を生成します。

- Windows x64のインストーラー。
- Windows ARM64のインストーラー。
- Nothing Phone (3)用、Android ARM64の署名済みrelease APK。

公開forkの成果物が、そのまま公開バイナリにならないよう、アップロード前に
ageで暗号化します。リポジトリに置くのは`.github/artifact-recipient.txt`の
**公開鍵だけ**です。秘密鍵とパスワードはActions Secretsへ保存し、
ソースにはコミットしません。手元のZIPはバックアップです。
GitHub Releaseは作成しません。名称・アイコンの変更や一般向けの配布は
この作業の対象外です。公開配布する場合は本家の`TRADEMARKS.md`に従ってください。

Actionsがforkで無効になっている場合は、リポジトリのActionsタブで有効にします。
手動実行では、対象ブランチに`ja-v0.1.5`を指定してください。

## 初回のSecrets登録

オーナーのPCにGitHub CLI（`gh`）が必要です。`gh auth login`で自分の
アカウントに認証済みであることを確認します。
`scripts/Register-Secrets.ps1`と`NectarLink-ja-build-keys-private.zip`を
同じフォルダーに置き、PowerShellで次を実行します。

```powershell
powershell -ExecutionPolicy Bypass -File .\Register-Secrets.ps1
```

次の3つのリポジトリSecretsを登録します。

| 名前 | 内容 |
|---|---|
| `ANDROID_KEYSTORE` | 配布済みAPKと同じ署名鍵（Base64） |
| `ANDROID_KEYSTORE_PASSWORD` | 署名鍵のパスワード |
| `ARTIFACT_AGE_IDENTITY` | 成果物の復号鍵の復旧用コピー |

署名鍵はActionsの一時フォルダーへ復元し、署名後に削除します。
復号鍵は復旧用の保管です。CIでの暗号化には公開鍵だけを使います。
Secretsの値はAPIで読み戻せないため、手元のバックアップも保管します。

## 回収

1. 自分のリポジトリから暗号化されたActions artifactをダウンロード。
2. ageの復号鍵で`.age`を復号し、`manifest.json`のSHA-256と照合。
3. 署名済みAndroid APKを`apksigner verify --verbose --print-certs`と
   `zipalign -c -P 16 -v 4`で検証。
4. 復号したWindowsインストーラーと、署名済みAPKを個人用に受け渡し。

次回も同じ鍵で更新できるよう、**復号鍵・Android署名鍵・パスワードを
リポジトリに入れず保管**してください。

## 導入時の注意

- Androidの公式版とは署名が異なるため、公式版への上書き更新はできません。
  公式版を削除する場合は、保存データとペアリングが消えることを確認してください。
- アプリIDとWindowsのインストール先は本家と共通です。公式版と別アプリとして
  並べて使う構成ではありません。
- 本家の自動更新を適用すると、日本語化は維持されません。設定で自動更新を
  オフにし、この作業ブランチからのビルドを使ってください。
- Windows版は個人ビルドのため、発行元のAuthenticode署名はありません。
- 日本語を手動で選ぶ場合は、Settings → Appearance → Language → 日本語。

Phone Link（スマートフォン連携）やWindowsにリンクの設定には変更を加えません。
