# ============================================================
# 小学英语点读 · Android APK 打包配置（buildozer）
# 适用：GitHub Actions 云端一键打包（.github/workflows/build-apk.yml）
# 也可在本机 Linux / WSL 执行：buildozer android debug
# 首次打包自动下载 Android SDK / NDK（约 2~3 GB），云端有缓存后明显提速。
# ============================================================

[app]

# 应用名称（桌面图标下方显示）
title = 小学英语点读

# 包名（英文小写，不能含中文、空格、连字符以外字符）
package.name = englishstudy
# 包域名（倒写域名，保证包名全局唯一）
source.org = org.pep.study

# 应用版本号（改这里即改 APK 版本；Actions 产物名会带上该版本）
version = 1.0.0

# 源码目录（当前文件夹，main.py 为入口）
source.dir = .

# 打包包含的文件类型：代码 + 图标/图片 + 内置中文字体。
# 不要写 json：运行时存档在应用私有目录生成，仓库内若残留旧存档也不会被打进包。
source.include_exts = py,png,jpg,ttf

# 运行时依赖（打进 APK 内）：
#   python3  解释器；kivy 界面框架；plyer TTS 朗读兜底。
#   jnius 由 python-for-android 内置，这里不要重复列出。
requirements = python3, kivy, plyer

# python-for-android 分支：master 为稳定版，兼容当前 API/NDK 组合
p4a.branch = master

# 屏幕方向：auto = 跟随平板 / 手机自动旋转
android.orientation = auto

# 目标 / 最低安卓版本（安卓 5.0 及以上均可安装）
android.api = 33
android.minapi = 21
android.sdk = 24
android.ndk = 25b

# 朗读使用系统自带离线语音，不联网，因此不申请 INTERNET 权限
android.permissions =

# 软键盘弹出时窗口自动缩放，避免输入区域被遮挡
android.window_softinput_mode = resize

# 自动接受 Android SDK 许可协议，避免云端/本机首次打包卡在交互确认
android.accept_sdk_license = True

# 允许应用数据在系统备份时保留
android.allow_backup = True

# 启动屏背景色（米黄，与界面配色一致）
android.presplash_color = #FFF6E5

# 图标（可选：把 512x512 的 icon.png 放到本目录，再取消下一行注释）
# icon.filename = %(source.dir)s/icon.png

[buildozer]
# 日志级别：2 = 详细；1 = 精简；0 = 只报错
log_level = 2

# 打包中间产物缓存目录（放在本目录，便于 GitHub Actions 命中缓存、复用编译结果）
cache_dir = .buildozer

# 缺失图标等问题只警告、不中断打包
warn_on_root = 0
