# c4002-python

[![PyPI version](https://img.shields.io/pypi/v/c4002-python.svg)](https://pypi.org/project/c4002-python/)
[![Test & Lint](https://github.com/nobudev7/c4002-python/actions/workflows/test.yml/badge.svg)](https://github.com/nobudev7/c4002-python/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

[🇺🇸 English](README.md) | [🇯🇵 日本語](README.ja.md)

**DFRobot C4002 (SEN0691) 24GHz ミリ波モーション&静的プレゼンスモジュール**用の Python ドライバおよび CLI ツール。

堅牢な UART パケットフレーミング、リアルタイムテレメトリデコード（人の存在検出、距離、速度、移動方向、照度）、部屋の背景ノイズの自動キャリブレーション、および Raspberry Pi などの Linux システムにおけるオプションのデジタル OUT ピン監視機能を提供します。

---

> [!IMPORTANT]
> **免責事項**: 本ライブラリは独立したオープンソースプロジェクトです。DFRobot 社との提携、同社による保守や推奨を受けているものではありません。すべての製品名、ロゴ、ブランドは各所有者の商標または登録商標です。

---

![DFRobot C4002 mmWave Sensor](docs/images/c4002_sensor.jpeg)

## 特長

* **完全なテレメトリデコード**: C4002 センサーからの 32 バイトのバイナリ通知フレームを解析。
  * **静止存在検知（Static Presence）**: 静止している人（呼吸、着席など）を距離 (m) および信号強度（0〜100）とともに検知。
  * **動体トラッキング（Motion Tracking）**: 距離 (m)、速度 (m/s)、信号強度（0〜100）、および移動方向（接近: Approaching / 離脱: Away）を測定。
  * **環境照度（Ambient Light）**: 搭載された照度センサーの強度（Lux）をデコード。
  * **ゲートビットマスクと保持タイマー（Gate Bitmasks & Hold Timers）**: アクティブな検知ゲート番号と存在消失までのカウントダウン機能。
* **自動環境ノイズキャリブレーション**: 部屋の電波反射をサンプリングして背景ノイズ基準値を保存し、誤検知を防止する組み込みルーチン。
* **高信頼なチェックサム検証**: 16ビットパケットチェックサムを検証し、破損データを自動破棄。
* **ハードウェア非依存**: Raspberry Pi Zero W で動作確認済みですが、すべての Raspberry Pi および Linux、macOS、Windows 上の一般的な USB-UART TTL シリアル変換アダプタで動作するはずです。
* **オプションの GPIO 監視**: `RPi.GPIO` によるモジュールのデジタル OUT ピン監視をサポート（GPIO が利用できない環境では自動的にグレースフルフォールバック）。

---

## ハードウェア配線

C4002 は **3.6V 〜 5.5V** の電源、および **3.3V TTL UART ロジックレベル**で動作します。Raspberry Pi の 5V 電源ピンから直接給電できます。

<!-- ![Raspberry Pi 配線図](docs/images/wiring_diagram.png) -->
```
  Raspberry Pi GPIO ヘッダー                DFRobot C4002
 ┌─────────────────────────┐               ┌─────────────┐
 │ Pin 2  [5V]             ├───────────────┤ VIN         │
 │ Pin 6  [GND]            ├───────────────┤ GND         │
 │ Pin 8  [GPIO 14 / TXD]  ├───────────────┤ RX          │
 │ Pin 10 [GPIO 15 / RXD]  ├───────────────┤ TX          │
 │ Pin 11 [GPIO 17]        ├───────────────┤ OUT (opt)   │
 └─────────────────────────┘               └─────────────┘
```

### ピン配置表（Raspberry Pi 40ピンヘッダー）

| C4002 ピン | Raspberry Pi ピン | ヘッダーピン番号 | 説明 |
| :--- | :--- | :--- | :--- |
| **VIN** | 5V 電源 | Pin 2 または 4 | 電源供給 (3.6V 〜 5.5V) |
| **GND** | グランド | Pin 6, 9, または 14 | 共通グランド |
| **TX** | GPIO 15 (RXD0) | Pin 10 | センサー TX $\rightarrow$ Pi RXD |
| **RX** | GPIO 14 (TXD0) | Pin 8 | センサー RX $\leftarrow$ Pi TXD |
| **OUT** *(オプション)* | GPIO 17 | Pin 11 | デジタル存在インジケータ (HIGH = 検知) |


### Raspberry Pi シリアルポートの設定

ハードウェア UART を有効にし、シリアルログインコンソールを無効にする設定を行います:

1. `sudo raspi-config` を実行
2. **Interface Options** $\rightarrow$ **Serial Port** を選択
3. 「Would you like a login shell to be accessible over serial?」（シリアル接続でログインシェルを有効にしますか？） $\rightarrow$ **No** を選択
4. 「Would you like the serial port hardware to be enabled?」（シリアルポートハードウェアを有効にしますか？） $\rightarrow$ **Yes** を選択
5. Raspberry Pi を再起動: `sudo reboot`

プライマリシリアルポートは `/dev/serial0` として利用可能になります。

---

## インストール

### pip によるインストール（推奨）

[PyPI](https://pypi.org/project/c4002-python/) から最新リリースをインストールします:

```bash
# 標準インストール
pip install c4002-python

# Raspberry Pi GPIO サポート（オプション）を含む場合
pip install "c4002-python[gpio]"
```

### GitHub から直接インストール

GitHub から直接開発版をインストールする場合:

```bash
# 標準インストール
pip install git+https://github.com/nobudev7/c4002-python.git

# Raspberry Pi GPIO サポート（オプション）を含む場合
pip install "c4002-python[gpio] @ git+https://github.com/nobudev7/c4002-python.git"
```

### ソースコードからインストール（ローカル開発用）

```bash
git clone https://github.com/nobudev7/c4002-python.git
cd c4002-python
pip install -e .
```

Raspberry Pi GPIO サポート（オプション）を含める場合:

```bash
pip install -e ".[gpio]"
```

---

## クイックスタート

```python
import time
from c4002 import C4002Sensor, TargetState

# デフォルトのシリアルポートとオプションの GPIO 17 でセンサーを初期化
sensor = C4002Sensor(port="/dev/serial0", baudrate=115200, out_pin=17)
sensor.connect()

try:
    while True:
        data = sensor.read_packet()
        if data and not getattr(data, "is_calibrating", False):
            print(f"State: {data.target_state_name} | Light: {data.ambient_light_lux} Lux")
            if data.presence_detected:
                print(f"  Presence: {data.presence_distance_m} m (Energy: {data.presence_energy}/100)")
                if data.target_state == TargetState.MOTION:
                    print(f"  Motion: {data.motion_distance_m} m at {data.motion_speed_m_s} m/s ({data.motion_direction_name})")
        time.sleep(0.5)
except KeyboardInterrupt:
    sensor.close()
```

コンテキストマネージャとしての使用例:

```python
with C4002Sensor(port="/dev/serial0") as sensor:
    data = sensor.read_packet()
    if data:
        print("Presence:", data.presence_detected)
```

---

## オンボード LED 制御（消灯 / ステルスモード）

C4002 モジュールには 2 つのオンボード LED が搭載されています:
* **青色 RUN LED**: 動作 / 電源インジケータ（点滅または青色点灯）。
* **OUT LED**: 検知インジケータ（存在または動体を検知した際に点灯）。

UART 経由のソフトウェア制御で両方の LED を制御または完全に消灯できます:

```python
from c4002 import C4002Sensor, LedMode

with C4002Sensor(port="/dev/serial0") as sensor:
    # 両方の LED を消灯（ステルス / 寝室モード）
    sensor.turn_off_leds()

    # または各 LED を個別に制御:
    sensor.set_run_led(False)       # 青色 RUN LED を消灯
    sensor.set_out_led(False)       # 検知 OUT LED を消灯
    sensor.set_run_led(True)        # 青色 RUN LED を再点灯
    sensor.set_led(run_led=LedMode.OFF, out_led=LedMode.OFF)
```

サンプルスクリプトでは、`--led-off` フラグを指定して実行できます:

```bash
python3 examples/basic_monitor.py --led-off
python3 examples/minute_aggregator.py --led-off
```

> [!NOTE]
> センサーの検知しきい値と同様に、LED の状態はレーダーモジュール上の揮発性メモリに保存されます。センサーの電源が再投入された場合（電源の抜き差しや Raspberry Pi の再起動時など）、モジュールはハードウェアのデフォルト状態（RUN LED 点灯）に戻ります。消灯状態を維持したい場合は、スクリプトやデーモンの起動時に `turn_off_leds()` を呼び出してください。

---

## 環境背景ノイズのキャリブレーション

24GHz レーダー波は微細な動きを検知するため、反射物（金属製家具、扇風機、揺れるカーテンなど）によって無人の部屋でも誤検知が発生することがあります。

本センサーには自動背景ノイズキャリブレーション機能が組み込まれています:

```bash
python3 examples/auto_calibrate.py
```

1. スクリプトを実行します。
2. 10 秒以内に部屋から退出します。
3. センサーが静的な背景反射をサンプリングし動的ノイズしきい値を保存する間、30 秒間部屋を無人の状態に保ちます。

---

## 1分間隔の時系列データロギング（集計）

一時的な移動（例: 誰かが 10 秒間部屋を通り抜けた場合など）を見逃さずに、グラフ描画用の CSV ファイルへ存在データを記録する場合:

```bash
python3 examples/minute_aggregator.py --output presence_1min_timeseries.csv
```

* センサーテレメトリを 1 Hz で継続的にサンプリングし、1 分単位の行に集計します。
* グラフ作成に適したメトリクスを生成します:
  * `occupancy_pct`: 該当する 1 分間における在室率（`0.0% 〜 100.0%`）。
  * `avg_distance_m`: 平均存在距離（存在検知がアクティブな間のみ算出）。
  * `max_motion_energy`: その時間枠内で記録された最大移動エネルギー（`0 〜 100`）。
  * `avg_light_lux`: 平均環境照度。

---

## テレメトリデータリファレンス

`sensor.read_packet()` は以下の属性を持つ `TelemetryData` オブジェクトを返します:

| 属性 | 型 | 単位 / 範囲 | 説明 |
| :--- | :--- | :--- | :--- |
| `target_state` | `TargetState` | Enum (`0`, `1`, `2`) | `NO_TARGET`, `STATIC_PRESENCE`, または `MOTION` |
| `target_state_name` | `str` | 文字列 | 人間が判読可能な状態名 |
| `presence_detected` | `bool` | `True` / `False` | 存在または動体を検知している場合は `True` |
| `ambient_light_lux` | `float` | Lux (0.0 〜 6553.5) | オンボード照度センサーの照度値（注: 0.0〜6553.5 は Python/プロトコル上の値の範囲であり、実際のセンサー感度範囲は約 0〜50 Lux です） |
| `presence_distance_m` | `float` | メートル | 静止存在ターゲットまでの距離 |
| `presence_energy` | `int` | `0` 〜 `100` | 静止ターゲットの反射信号強度 |
| `presence_countdown_s` | `int` | 秒 | 存在フラグがクリアされるまでの遅延カウントダウン |
| `motion_distance_m` | `float` | メートル | 移動ターゲットまでの距離 |
| `motion_speed_m_s` | `float` | m/s | 移動ターゲットの視線方向速度（Radial Speed） |
| `motion_energy` | `int` | `0` 〜 `100` | 移動ターゲットの反射信号強度 |
| `motion_direction` | `MotionDirection` | Enum (`0`, `1`, `2`) | `AWAY`（離脱）, `NO_DIRECTION`（方向なし）, または `APPROACHING`（接近） |
| `gate_bitmask` | `int` | ビットマスク | アクティブな距離ゲートを表すビットフラグ |

---

## 単体テストの実行

記録済みの生テレメトリパケットを使用するため、実際のハードウェアが接続されていなくても単体テストを実行できます:

```bash
# 標準の Python unittest を使用する場合
PYTHONPATH=src python3 -m unittest discover -s tests -p "test_*.py"

# または pytest を使用する場合（インストールされている場合）
PYTHONPATH=src pytest -v tests/
```

---

## 参考資料・ドキュメント

* [DFRobot C4002 製品 Wiki (SEN0691)](https://wiki.dfrobot.com/sen0691)
* [DFRobot 公式 Arduino C4002 ライブラリ](https://github.com/DFRobot/DFRobot_C4002)

---

## ライセンス

本プロジェクトは [MIT License](LICENSE) の下で公開されています。
