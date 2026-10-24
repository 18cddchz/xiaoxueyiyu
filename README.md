# 小学英语点读 · GitHub Actions 云端一键打包

把这个文件夹整体上传到一个 GitHub 仓库，点一下按钮，云端自动编译出安卓 APK，
构建页直接下载安装包——**本机不需要装 Linux、JDK、SDK，也不用配环境**。

---

## 一、仓库目录结构（上传时保持这个层级，路径不能错）

```
仓库根目录/
├── main.py                          # 程序主文件（buildozer 固定入口名，不要改名）
├── DroidSansFallback.ttf           # 内置中文字体（不要删除）
├── buildozer.spec                   # 打包配置（应用名/包名/版本/依赖/权限，已配好）
├── requirements-build.txt          # 云端打包机工具链版本（一般不用动）
├── .gitignore                       # 忽略打包缓存与产物，不入库
├── README.md                        # 本指南
└── .github/
    └── workflows/
        └── build-apk.yml            # GitHub Actions 打包脚本（路径必须是这一级）
```

> 关键检查：上传后在 GitHub 网页上要能看到 `.github/workflows/build-apk.yml` 这条路径，
> 不能把 `.github` 套在别的文件夹里，否则 Actions 识别不到工作流。

---

## 二、上传到 GitHub（三步）

### 1. 新建仓库

登录 GitHub → 右上角 **+** → **New repository**：

- 仓库名随便填，例如 `englishstudy-apk`；
- **Public（公开）** 推荐：公开仓库用 GitHub Actions 免费、不限构建时长；
  选 **Private（私有）** 也可以，免费额度每月 2000 分钟 Linux 构建，足够日常打包；
- **不要**勾选 “Add a README”、不要勾选初始化 `.gitignore`（避免和本仓库文件冲突）；
- 点 **Create repository**。

### 2. 上传本文件夹里的全部文件

在新建仓库页面选 **uploading an existing file**，把本目录下的文件**连同层级**一起拖进去：

- `main.py`、`DroidSansFallback.ttf`、`buildozer.spec`、`requirements-build.txt`、
  `.gitignore`、`README.md` 放到仓库根；
- 把 `.github` 整个文件夹拖上去，确认网页里出现
  `.github/workflows/build-apk.yml`；
- 页面底部点 **Commit changes** 提交。

> 命令行方式（可选，习惯用 Git 的人）：
>
> ```bash
> cd 本文件夹所在目录
> git init
> git add .
> git commit -m "init: english study app, github actions build"
> git branch -M main
> git remote add origin https://github.com/<你的用户名>/englishstudy-apk.git
> git push -u origin main
> ```

### 3. 确认工作流已加载

进入仓库顶部 **Actions** 标签页，左侧能看到 **Build Android APK** 这个工作流，
说明脚本被识别到了。

---

## 三、一键打包（两种触发方式）

### 方式 A：手动触发（推荐第一次用）

1. 仓库页 **Actions** → 左侧选 **Build Android APK**；
2. 右侧点 **Run workflow** → 绿色 **Run workflow** 按钮；
3. 页面出现一条正在运行的任务，黄色圆点表示构建中。

### 方式 B：推送代码自动打包

往 `main` 或 `master` 分支提交代码时，只要改动了
`main.py`、`buildozer.spec`、`DroidSansFallback.ttf`、`requirements-build.txt`
或工作流文件，就会自动开始打包；改 README 等非代码文件不会触发。

---

## 四、等待构建完成

- **第一次打包最慢**：云端要下载 Android SDK / NDK（约 2~3 GB）并编译，
  通常 **1~2 小时**，保持页面不要关闭；
- **第二次起命中缓存**（SDK/NDK/编译中间结果已缓存），一般 **20~40 分钟**；
- 任务前出现 **绿色对勾 ✅** = 成功；**红色叉号 ❌** = 失败，点进任务
  最后一步 `Upload build logs on failure` 下载日志排查（见第六节）。

> 构建日志里大量滚动文字和 `WARNING` 都属正常，只有末尾 `ERROR` 且任务变红才算失败。

---

## 五、下载 APK 并安装到平板 / 手机

### 1. 下载安装包

1. 点进成功的那次任务；
2. 页面最底部 **Artifacts（产物）** 区，看到
   `englishstudy-v1.0.0-r<编号>-debug`；
3. 点它下载，得到一个 zip，解压后里面就是
   `englishstudy-1.0.0-debug.apk`。

### 2. 安装到安卓设备

1. 把 APK 通过微信文件传输助手、数据线、U盘或邮箱传到平板/手机；
2. 设备首次安装会提示“**未知来源应用**”，按提示允许后返回安装；
3. 桌面出现 **小学英语点读** 图标，点开即用；
4. 覆盖安装旧版本前，先卸载旧版（debug 签名每次一致，多数情况可直接覆盖；
   闪退或签名冲突就先卸载再装）。

---

## 六、常用修改说明

| 想改的内容 | 改哪里 |
|---|---|
| 应用版本号 | `buildozer.spec` 里的 `version = 1.0.0`（同步影响 APK 文件名） |
| 应用显示名称 | `buildozer.spec` 里的 `title = 小学英语点读` |
| 包名 / 全局应用标识 | `buildozer.spec` 里 `package.name`、`source.org`（改包名会像新 App，覆盖安装需先卸载） |
| 单词、句子、短文 | 直接改 `main.py` 里的 `word_data` 词库 |
| 应用图标 | 把 512×512 的 `icon.png` 放到仓库根，去掉 `buildozer.spec` 里 `icon.filename` 一行的注释 |
| 联网权限 | 朗读用系统离线语音，默认不申请 `INTERNET`；若将来需要联网功能，在 `android.permissions` 里补上 |

修改后提交推送，或在 Actions 页手动 **Run workflow** 即可重新出包。

---

## 七、常见问题排查

### 7.1 任务变红，先看失败日志

点进失败任务 → 展开最后一步 `Upload build logs on failure` 下载产物，
里面是 `.buildozer` / `~/.buildozer` 下的日志；把最末尾带 `ERROR` 的段落对照下表。

### 7.2 中文显示成方块

- 确认仓库根存在 `DroidSansFallback.ttf`；
- 确认 `buildozer.spec` 的 `source.include_exts = py,png,jpg,ttf` 里含有 `ttf`；
- 删掉缓存重新打包：在仓库根删 `.buildozer/` 与 `bin/`（Actions 上一次任务里
  可在工作流加 `run: rm -rf .buildozer` 步骤，或直接清空缓存重跑）。

### 7.3 点朗读没有声音

这通常**不是 App 故障**：App 调用设备系统自带离线语音引擎。

- 进设备 **设置 → 语言和输入法（或辅助功能）→ 文字转语音输出**：
  确认语音引擎已启用，并下载 **English (US)** 英文语音包；
- 调大媒体音量，关闭勿扰 / 静音；
- 在 App 里切换“慢 / 正常”语速试听一句英文，判断引擎是否工作。

### 7.4 报 `cython` / 编译相关错误

`requirements-build.txt` 已把 Cython 锁在 `0.29.34`（p4a 配方要求 0.29.x，
3.x 会编译失败）；不要手动升级 Cython。若缓存里残留旧版本，清空
`~/.buildozer` 与 `.buildozer` 缓存后重跑。

### 7.5 构建超时或缓存失效

- 首次下载 SDK/NDK 占时长，正常等待即可；
- Actions 缓存 key 绑定 `buildozer.spec` 内容，改动 spec 会重建缓存，属预期行为；
- 私有仓库留意月度构建分钟额度。

### 7.6 不想用云端打包（本地备选）

见同目录 `打包安装指南.md`（Windows + WSL 本地 `buildozer android debug` 路线）。

---

## 附：构建机环境（已在工作流里配好，一般无需改动）

- 系统：`ubuntu-22.04`；JDK 17（Temurin）；Python 3.10；
- 打包器：`buildozer`（1.5–1.7）、`cython==0.29.34`、`virtualenv`；
- Android：目标 API 33、最低 API 21、NDK 25b、p4a `master` 稳定分支；
- 缓存目录：`$HOME/.buildozer`（SDK/NDK/gradle）与 `.buildozer`（编译中间结果）。
