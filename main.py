from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.uix.scrollview import ScrollView
from kivy.storage.jsonstore import JsonStore
from kivy.core.text import LabelBase
from kivy.graphics import Color, Rectangle
from kivy.utils import platform
from kivy.uix.popup import Popup
import json
import random
import os
import time
# ===================== 界面配色 =====================
BG_COLOR = [1, 0.97, 0.86, 1]
TEXT_COLOR = [0, 0, 0, 1]
TIME_RED_COLOR = [0.9, 0, 0, 1]
RIGHT_COLOR = [0, 0.7, 0, 1]
WRONG_COLOR = [0.8, 0, 0, 1]
RED_CN = "#dd0000"  # 中文释义红色
# 全局字号基准，运行可按钮动态加减
BASE_FONT = 40
FONT_BUTTON = 48   # 按钮文字固定48
# ========== 字体：内置/根目录多级回退，保证打包后中文正常 ==========
def _pick_font():
    # 1) APK 内置字体（buildozer 已把 ttf 打进去）
    try:
        import kivy.resources as _res
        _f = _res.resource_find("DroidSansFallback.ttf")
        if _f and os.path.exists(_f):
            return _f
    except Exception:
        pass
    # 2) 手机/平板根目录旧路径（Pydroid3 调试时用）
    if os.path.exists("/storage/emulated/0/DroidSansFallback.ttf"):
        return "/storage/emulated/0/DroidSansFallback.ttf"
    return None
FONT_PATH = _pick_font()
try:
    if FONT_PATH:
        LabelBase.register(name="DroidSans", fn_regular=FONT_PATH)
        FONT_NAME = "DroidSans"
    else:
        FONT_NAME = None
except Exception as e:
    print("字体加载失败，使用系统默认字体", e)
    FONT_NAME = None
# ========= 安卓TTS语音模块（美式en‑US） =========
_tts_engine = None          # jnius 引擎实例（退出时 shutdown 用）
_tts_ready = False          # 引擎异步初始化是否完成
_tts_cls = None
_plyer_tts = None
_holder = {"ready": False}

if platform == "android":
    try:
        from jnius import autoclass, PythonJavaClass, java_method
        _TTS = autoclass("android.speech.tts.TextToSpeech")
        _Locale = autoclass("java.util.Locale")
        _PythonActivity = autoclass("org.kivy.android.PythonActivity")

        class _OnInitListener(PythonJavaClass):
            __javainterfaces__ = ["android/speech/tts/TextToSpeech$OnInitListener"]
            def __init__(self, holder):
                super().__init__()
                self._holder = holder
            @java_method("(I)V")
            def onInit(self, status):
                self._holder["ready"] = (status == 0)

        _activity = _PythonActivity.mActivity
        _tts_engine = _TTS(_activity, _OnInitListener(_holder))
        _tts_engine.setLanguage(_Locale.US)
        _tts_cls = _TTS
        # 引擎异步初始化，首次最多等待约 1.5 秒
        for _ in range(30):
            if _holder["ready"]:
                break
            time.sleep(0.05)
        _tts_ready = _holder["ready"]
    except Exception as e:
        print("jnius TTS 初始化失败，转 plyer 兜底:", e)
        _tts_engine = None
        _tts_ready = False

# jnius 不可用时用 plyer 兜底；桌面环境两者都不可用则静默降级，不崩溃
if _tts_engine is None:
    try:
        from plyer import tts as _plyer_tts
    except Exception:
        _plyer_tts = None

# 兼容旧代码：全局 tts 指向引擎，供 on_stop 调用 shutdown
tts = _tts_engine
TextToSpeech = _tts_cls
Locale = None

def speak_en(text, speed=1.0):
    clean_text = (text or "").replace("\n", " ").strip()
    if not clean_text:
        return False
    # 1) 优先 jnius 直连安卓原生引擎
    if platform == "android" and _tts_engine is not None and _tts_cls is not None:
        try:
            if not _tts_ready:
                for _ in range(20):
                    if _holder["ready"]:
                        _tts_ready = True
                        break
                    time.sleep(0.05)
            if _tts_ready:
                _tts_engine.setSpeechRate(float(speed))
                _tts_engine.speak(clean_text, _tts_cls.QUEUE_FLUSH, None)
                return True
        except Exception as e:
            print("jnius 朗读失败:", e)
    # 2) plyer 兜底
    if _plyer_tts is not None:
        try:
            _plyer_tts.speak(clean_text)
            return True
        except Exception as e:
            print("plyer TTS 朗读失败:", e)
    return False
# ===================== 人教PEP三起课本词库（带音标、课本例句、知识点） =====================
word_data = {
    "3年级上册": {
        "words": [
            {"en":"ruler","phonetic":"/ˈruːlə(r)/","cn":"尺子","sentence_en":"Show me your ruler.","sentence_cn":"给我看看你的尺子。","note":"文具类名词，用来量长度、画直线"},
            {"en":"pencil","phonetic":"/ˈpensl/","cn":"铅笔","sentence_en":"I have a pencil.","sentence_cn":"我有一支铅笔。","note":"可以书写，字迹能够用橡皮擦掉"},
            {"en":"eraser","phonetic":"/ɪˈreɪzə(r)/","cn":"橡皮","sentence_en":"I have an eraser.","sentence_cn":"我有一块橡皮。","note":"an后面接元音开头单词eraser"},
            {"en":"crayon","phonetic":"/ˈkreɪɒn/","cn":"蜡笔","sentence_en":"Show me your crayon.","sentence_cn":"给我看看你的蜡笔。","note":"画画涂色的彩色笔"},
            {"en":"bag","phonetic":"/bæɡ/","cn":"包；书包","sentence_en":"I have a bag.","sentence_cn":"我有一个书包。","note":"用来装书本文具"},
            {"en":"pen","phonetic":"/pen/","cn":"钢笔","sentence_en":"Show me your pen.","sentence_cn":"给我看看你的钢笔。","note":"墨水书写，字迹不易擦除"},
            {"en":"book","phonetic":"/bʊk/","cn":"书","sentence_en":"Open your book.","sentence_cn":"打开你的书。","note":"书本，可数名词"},
            {"en":"red","phonetic":"/red/","cn":"红色","sentence_en":"I see red.","sentence_cn":"我看见红色。","note":"颜色形容词，可修饰物品"},
            {"en":"yellow","phonetic":"/ˈjeləʊ/","cn":"黄色","sentence_en":"Colour it yellow.","sentence_cn":"把它涂成黄色。","note":"涂色句型 colour it +颜色"},
            {"en":"green","phonetic":"/ɡriːn/","cn":"绿色","sentence_en":"Show me green.","sentence_cn":"给我看看绿色。","note":"大自然小草树叶的颜色"},
            {"en":"blue","phonetic":"/bluː/","cn":"蓝色","sentence_en":"I like blue.","sentence_cn":"我喜欢蓝色。","note":"天空大海的颜色"},
            {"en":"cat","phonetic":"/kæt/","cn":"猫","sentence_en":"It’s a cat.","sentence_cn":"它是一只猫。","note":"动物名词，cat辅音开头用a"},
            {"en":"dog","phonetic":"/dɒɡ/","cn":"狗","sentence_en":"What’s this? It’s a dog.","sentence_cn":"这是什么？它是一只狗。","note":"宠物动物"},
            {"en":"monkey","phonetic":"/ˈmʌŋki/","cn":"猴子","sentence_en":"Look at the monkey.","sentence_cn":"看这只猴子。","note":"会爬树的小动物"},
            {"en":"bird","phonetic":"/bɜːd/","cn":"鸟","sentence_en":"It’s a bird.","sentence_cn":"它是一只鸟。","note":"有翅膀可以在天上飞"}
        ],
        "sentences": [
            {"en":"Hello! I'm Wu Yifan.","phonetic":"","cn":"你好！我是吴一凡。","sentence_en":"Hello! I'm Wu Yifan.","sentence_cn":"你好！我是吴一凡。","note":"初次见面自我介绍句型 I'm+名字"},
            {"en":"Good morning.","phonetic":"","cn":"早上好。","sentence_en":"Good morning.","sentence_cn":"早上好。","note":"上午见面问候语"},
            {"en":"Nice to meet you.","phonetic":"","cn":"很高兴见到你。","sentence_en":"Nice to meet you.","sentence_cn":"很高兴见到你。","note":"第一次认识别人礼貌用语"},
            {"en":"What's your name? My name's John.","phonetic":"","cn":"你叫什么名字？我叫约翰。","sentence_en":"What's your name? My name's John.","sentence_cn":"你叫什么名字？我叫约翰。","note":"询问对方名字的核心句型"}
        ],
        "articles": [
            {"en":"Hello, my name is Amy.\nI have a new bag.\nIt is blue.\nI like my bag.","phonetic":"","cn":"你好，我叫艾米。\n我有一个新书包。\n它是蓝色的。\n我喜欢我的书包。","sentence_en":"Hello, my name is Amy.\nI have a new bag.\nIt is blue.\nI like my bag.","sentence_cn":"你好，我叫艾米。\n我有一个新书包。\n它是蓝色的。\n我喜欢我的书包。","note":"短篇阅读练习，学习have、like用法"}
        ]
    },
    "3年级下册": {
        "words": [
            {"en":"UK","phonetic":"/ˌjuːˈkeɪ/","cn":"英国","sentence_en":"I’m from the UK.","sentence_cn":"我来自英国。","note":"国家缩写前面要加the"},
            {"en":"Canada","phonetic":"/ˈkænədə/","cn":"加拿大","sentence_en":"I’m from Canada.","sentence_cn":"我来自加拿大。","note":"北美洲国家名词"},
            {"en":"USA","phonetic":"/ˌjuːesˈeɪ/","cn":"美国","sentence_en":"She is from the USA.","sentence_cn":"她来自美国。","note":"美利坚合众国缩写，加the"},
            {"en":"China","phonetic":"/ˈtʃaɪnə/","cn":"中国","sentence_en":"I’m from China.","sentence_cn":"我来自中国。","note":"我们的国家，不加the"},
            {"en":"she","phonetic":"/ʃiː/","cn":"她","sentence_en":"She is a student.","sentence_cn":"她是一名学生。","note":"指代女生，第三人称单数"},
            {"en":"student","phonetic":"/ˈstjuːdnt/","cn":"学生","sentence_en":"He is a student.","sentence_cn":"他是一名学生。","note":"在校读书的学生"},
            {"en":"teacher","phonetic":"/ˈtiːtʃə(r)/","cn":"教师","sentence_en":"This is my teacher.","sentence_cn":"这是我的老师。","note":"教书的老师"},
            {"en":"he","phonetic":"/hiː/","cn":"他","sentence_en":"He is my dad.","sentence_cn":"他是我的爸爸。","note":"指代男生"},
            {"en":"father","phonetic":"/ˈfɑːðə(r)/","cn":"父亲；爸爸","sentence_en":"This is my father.","sentence_cn":"这是我的爸爸。","note":"书面正式叫法"},
            {"en":"mother","phonetic":"/ˈmʌðə(r)/","cn":"母亲；妈妈","sentence_en":"This is my mother.","sentence_cn":"这是我的妈妈。","note":"书面正式叫法"},
            {"en":"sister","phonetic":"/ˈsɪstə(r)/","cn":"姐妹","sentence_en":"She is my sister.","sentence_cn":"她是我的姐妹。","note":"姐姐或者妹妹通用"},
            {"en":"brother","phonetic":"/ˈbrʌðə(r)/","cn":"兄弟","sentence_en":"He is my brother.","sentence_cn":"他是我的兄弟。","note":"哥哥或者弟弟通用"},
            {"en":"thin","phonetic":"/θɪn/","cn":"瘦的","sentence_en":"He is thin.","sentence_cn":"他很瘦。","note":"描述人身材瘦"},
            {"en":"fat","phonetic":"/fæt/","cn":"胖的","sentence_en":"The pig is fat.","sentence_cn":"这头猪胖胖的。","note":"形容肉肉多"},
            {"en":"tall","phonetic":"/tɔːl/","cn":"高的","sentence_en":"My dad is tall.","sentence_cn":"我的爸爸个子很高。","note":"形容个子高"},
            {"en":"short","phonetic":"/ʃɔːt/","cn":"矮的；短的","sentence_en":"He is short.","sentence_cn":"他个子矮。","note":"一词两义：个子矮、东西短"},
            {"en":"apple","phonetic":"/ˈæpl/","cn":"苹果","sentence_en":"I like apples.","sentence_cn":"我喜欢苹果。","note":"水果名词，喜欢一类用复数apples"},
            {"en":"banana","phonetic":"/bəˈnɑːnə/","cn":"香蕉","sentence_en":"Have some bananas.","sentence_cn":"吃点香蕉。","note":"香蕉复数bananas"}
        ],
        "sentences": [
            {"en":"Where are you from? I'm from China.","phonetic":"","cn":"你来自哪里？我来自中国。","sentence_en":"Where are you from? I'm from China.","sentence_cn":"你来自哪里？我来自中国。","note":"询问来自哪个国家重点句型"},
            {"en":"Who's that man? He's my father.","phonetic":"","cn":"那个男人是谁？他是我的爸爸。","sentence_en":"Who's that man? He's my father.","sentence_cn":"那个男人是谁？他是我的爸爸。","note":"询问远处男士是谁"},
            {"en":"Do you like oranges? Yes, I do.","phonetic":"","cn":"你喜欢橙子吗？是的，我喜欢。","sentence_en":"Do you like oranges? Yes, I do.","sentence_cn":"你喜欢橙子吗？是的，我喜欢。","note":"Do you like...一般疑问句问答"}
        ],
        "articles": [
            {"en":"I have a family.\nMy dad is tall.\nMy mum is nice.\nI love my family.","phonetic":"","cn":"我有一个家庭。\n我的爸爸很高。\n我的妈妈很和善。\n我爱我的家人。","sentence_en":"I have a family.\nMy dad is tall.\nMy mum is nice.\nI love my family.","sentence_cn":"我有一个家庭。\n我的爸爸很高。\n我的妈妈很和善。\n我爱我的家人。","note":"家庭主题小短文，学习be动词is用法"}
        ]
    },
    "4年级上册": {
        "words": [
            {"en":"classroom","phonetic":"/ˈklɑːsruːm/","cn":"教室","sentence_en":"This is my classroom.","sentence_cn":"这是我的教室。","note":"上课的房间，class+room合成词"},
            {"en":"window","phonetic":"/ˈwɪndəʊ/","cn":"窗户","sentence_en":"Open the window.","sentence_cn":"打开窗户。","note":"教室物品名词"},
            {"en":"blackboard","phonetic":"/ˈblækbɔːd/","cn":"黑板","sentence_en":"Clean the blackboard.","sentence_cn":"擦黑板。","note":"black+board合成词"},
            {"en":"light","phonetic":"/laɪt/","cn":"电灯","sentence_en":"Turn on the light.","sentence_cn":"打开电灯。","note":"turn on打开电器；turn off关闭电器"},
            {"en":"door","phonetic":"/dɔː(r)/","cn":"门","sentence_en":"Open the door.","sentence_cn":"开门。","note":"房间出入口"},
            {"en":"schoolbag","phonetic":"/ˈskuːlbæɡ/","cn":"书包","sentence_en":"My schoolbag is heavy.","sentence_cn":"我的书包很重。","note":"school+bag合成词"},
            {"en":"Chinese book","phonetic":"/ˌtʃaɪˈniːz bʊk/","cn":"语文书","sentence_en":"I have a Chinese book.","sentence_cn":"我有一本语文书。","note":"学科类书本"},
            {"en":"English book","phonetic":"/ˈɪŋɡlɪʃ bʊk/","cn":"英语书","sentence_en":"Where is my English book?","sentence_cn":"我的英语书在哪里？","note":"English开头必须大写E"},
            {"en":"strong","phonetic":"/strɒŋ/","cn":"强壮的","sentence_en":"He is strong.","sentence_cn":"他很强壮。","note":"形容人身体结实有力气"},
            {"en":"friendly","phonetic":"/ˈfrendli/","cn":"友好的","sentence_en":"She is friendly.","sentence_cn":"她待人很友好。","note":"形容词，friend朋友+ly变成形容词"},
            {"en":"quiet","phonetic":"/ˈkwaɪət/","cn":"安静的","sentence_en":"Be quiet.","sentence_cn":"保持安静。","note":"课堂指令常用短语"},
            {"en":"beef","phonetic":"/biːf/","cn":"牛肉","sentence_en":"I’d like some beef.","sentence_cn":"我想要一些牛肉。","note":"不可数名词，不加s"},
            {"en":"chicken","phonetic":"/ˈtʃɪkɪn/","cn":"鸡肉","sentence_en":"Have some chicken.","sentence_cn":"吃点鸡肉。","note":"表示鸡肉不可数；小鸡可数"},
            {"en":"noodles","phonetic":"/ˈnuːdlz/","cn":"面条","sentence_en":"I like noodles.","sentence_cn":"我喜欢面条。","note":"面条永远常用复数noodles"},
            {"en":"chopsticks","phonetic":"/ˈtʃɒpstɪks/","cn":"筷子","sentence_en":"Use chopsticks.","sentence_cn":"使用筷子。","note":"筷子总是复数形式"}
        ],
        "sentences": [
            {"en":"Let's clean the classroom.","phonetic":"","cn":"让我们打扫教室。","sentence_en":"Let's clean the classroom.","sentence_cn":"让我们打扫教室。","note":"Let's +动词原形，让我们一起做某事"},
            {"en":"What's in your schoolbag?","phonetic":"","cn":"你的书包里面有什么？","sentence_en":"What's in your schoolbag?","sentence_cn":"你的书包里面有什么？","note":"询问某处里面有什么物品"},
            {"en":"What would you like for dinner?","phonetic":"","cn":"晚餐你想吃什么？","sentence_en":"What would you like for dinner?","sentence_cn":"晚餐你想吃什么？","note":"点餐核心句型 would like想要"}
        ],
        "articles": [
            {"en":"Our classroom is big.\nWe have a blackboard.\nWe read books here.\nWe love our classroom.","phonetic":"","cn":"我们的教室很大。\n我们有一块黑板。\n我们在这里读书。\n我们爱我们的教室。","sentence_en":"Our classroom is big.\nWe have a blackboard.\nWe read books here.\nWe love our classroom.","sentence_cn":"我们的教室很大。\n我们有一块黑板。\n我们在这里读书。\n我们爱我们的教室。","note":"校园主题阅读短文"}
        ]
    },
    "4年级下册": {
        "words": [
            {"en":"first floor","phonetic":"/fɜːst flɔː(r)/","cn":"一楼","sentence_en":"It’s on the first floor.","sentence_cn":"它在一楼。","note":"first序数词第一；英美楼层习惯"},
            {"en":"second floor","phonetic":"/ˈsekənd flɔː(r)/","cn":"二楼","sentence_en":"The library is on the second floor.","sentence_cn":"图书馆在二楼。","note":"second序数词第二"},
            {"en":"library","phonetic":"/ˈlaɪbrəri/","cn":"图书馆","sentence_en":"Go to the library. Read a book.","sentence_cn":"去图书馆，读一本书。","note":"借书看书的地方"},
            {"en":"playground","phonetic":"/ˈpleɪɡraʊnd/","cn":"操场","sentence_en":"Go to the playground.","sentence_cn":"去操场。","note":"play+ground合成词运动场地"},
            {"en":"breakfast","phonetic":"/ˈbrekfəst/","cn":"早餐","sentence_en":"Have breakfast.","sentence_cn":"吃早饭。","note":"三餐名词：breakfast/lunch/dinner"},
            {"en":"lunch","phonetic":"/lʌntʃ/","cn":"午餐","sentence_en":"It’s time for lunch.","sentence_cn":"该吃午饭了。","note":"It's time for +名词 该做某事了"},
            {"en":"dinner","phonetic":"/ˈdɪnə(r)/","cn":"晚餐","sentence_en":"Dinner is ready.","sentence_cn":"晚饭准备好了。","note":"晚饭正餐"},
            {"en":"get up","phonetic":"/ɡet ʌp/","cn":"起床","sentence_en":"I get up at seven.","sentence_cn":"我七点钟起床。","note":"时间介词at+几点钟"},
            {"en":"go to school","phonetic":"/ɡəʊ tuː skuːl/","cn":"去上学","sentence_en":"I go to school at eight.","sentence_cn":"我八点去上学。","note":"固定短语go to school"},
            {"en":"cold","phonetic":"/kəʊld/","cn":"寒冷的","sentence_en":"It’s cold today.","sentence_cn":"今天天气很冷。","note":"描述天气it's+天气形容词"},
            {"en":"hot","phonetic":"/hɒt/","cn":"热的","sentence_en":"It’s hot in summer.","sentence_cn":"夏天天气很热。","note":"夏天天气热"},
            {"en":"warm","phonetic":"/wɔːm/","cn":"温暖的","sentence_en":"Spring is warm.","sentence_cn":"春天很温暖。","note":"春天温度舒服"},
            {"en":"cool","phonetic":"/kuːl/","cn":"凉爽的","sentence_en":"Autumn is cool.","sentence_cn":"秋天很凉爽。","note":"秋天凉快"},
            {"en":"sunny","phonetic":"/ˈsʌni/","cn":"晴朗的","sentence_en":"It’s sunny today.","sentence_cn":"今天天气晴朗。","note":"名词sun太阳+ny变形容词"},
            {"en":"tomato","phonetic":"/təˈmɑːtəʊ/","cn":"西红柿","sentence_en":"These are tomatoes.","sentence_cn":"这些是西红柿。","note":"复数tomatoes，o结尾加es"},
            {"en":"potato","phonetic":"/pəˈteɪtəʊ/","cn":"土豆","sentence_en":"Look at the potatoes.","sentence_cn":"看这些土豆。","note":"复数potatoes"}
        ],
        "sentences": [
            {"en":"Where is the library? It's on the second floor.","phonetic":"","cn":"图书馆在哪里？它在二楼。","sentence_en":"Where is the library? It's on the second floor.","sentence_cn":"图书馆在哪里？它在二楼。","note":"询问地点位置，楼层用介词on"},
            {"en":"What time is it? It's nine o'clock.","phonetic":"","cn":"几点了？九点了。","sentence_en":"What time is it? It's nine o'clock.","sentence_cn":"几点了？九点了。","note":"询问时间核心句型What time is it?"}
        ],
        "articles": [
            {"en":"I get up at seven.\nI go to school at eight.\nI have lunch at twelve.\nI go to bed at nine.","phonetic":"","cn":"我七点起床。\n我八点去上学。\n我十二点吃午饭。\n我九点上床睡觉。","sentence_en":"I get up at seven.\nI go to school at eight.\nI have lunch at twelve.\nI go to bed at nine.","sentence_cn":"我七点起床。\n我八点去上学。\n我十二点吃午饭。\n我九点上床睡觉。","note":"介绍一天作息时间小短文"}
        ]
    },
    "5年级上册": {
        "words": [
            {"en":"old","phonetic":"/əʊld/","cn":"老的；年纪大的","sentence_en":"He is old.","sentence_cn":"他年纪很大。","note":"反义词young年轻的"},
            {"en":"young","phonetic":"/jʌŋ/","cn":"年轻的","sentence_en":"My teacher is young.","sentence_cn":"我的老师很年轻。","note":"反义词old年老"},
            {"en":"funny","phonetic":"/ˈfʌni/","cn":"滑稽的；好笑的","sentence_en":"He is funny.","sentence_cn":"他很风趣幽默。","note":"描述人性格风趣"},
            {"en":"kind","phonetic":"/kaɪnd/","cn":"和蔼的","sentence_en":"She is kind.","sentence_cn":"她待人很和蔼。","note":"形容老师性格和善"},
            {"en":"strict","phonetic":"/strɪkt/","cn":"严厉的","sentence_en":"He is strict.","sentence_cn":"他很严格。","note":"strict but kind严格但是和蔼"},
            {"en":"polite","phonetic":"/pəˈlaɪt/","cn":"有礼貌的","sentence_en":"The boy is polite.","sentence_cn":"这个男孩懂礼貌。","note":"形容人懂礼貌守规矩"},
            {"en":"Monday","phonetic":"/ˈmʌndeɪ/","cn":"星期一","sentence_en":"We have PE on Monday.","sentence_cn":"星期一我们有体育课。","note":"星期前面介词on，首字母大写"},
            {"en":"Tuesday","phonetic":"/ˈtjuːzdeɪ/","cn":"星期二","sentence_en":"What do you have on Tuesdays?","sentence_cn":"星期二你有什么课？","note":"星期复数表示每星期二"},
            {"en":"wash","phonetic":"/wɒʃ/","cn":"洗","sentence_en":"I wash my clothes.","sentence_cn":"我洗衣服。","note":"wash clothes洗衣服"},
            {"en":"watch","phonetic":"/wɒtʃ/","cn":"看","sentence_en":"I watch TV on weekend.","sentence_cn":"我周末看电视。","note":"watch TV固定搭配看电视"},
            {"en":"read","phonetic":"/riːd/","cn":"读；阅读","sentence_en":"I read books on Saturday.","sentence_cn":"我周六看书。","note":"read books读书"},
            {"en":"sandwich","phonetic":"/ˈsænwɪtʃ/","cn":"三明治","sentence_en":"I’d like a sandwich.","sentence_cn":"我想要一个三明治。","note":"复数sandwiches"}
        ],
        "sentences": [
            {"en":"What's he like? He is young and kind.","phonetic":"","cn":"他是什么样的人？他年轻又和蔼。","sentence_en":"What's he like? He is young and kind.","sentence_cn":"他是什么样的人？他年轻又和蔼。","note":"询问人物性格外貌重点句型，不是问长相"},
            {"en":"What do you have on Mondays?","phonetic":"","cn":"星期一你有什么课？","sentence_en":"What do you have on Mondays?","sentence_cn":"星期一你有什么课？","note":"询问星期课程，星期前面介词on"}
        ],
        "articles": [
            {"en":"My English teacher is Ms Wang.\nShe is kind and funny.\nI like English class.\nI read books on weekends.","phonetic":"","cn":"我的英语老师是王老师。\n她和蔼又有趣。\n我喜欢英语课。\n我周末看书。","sentence_en":"My English teacher is Ms Wang.\nShe is kind and funny.\nI like English class.\nI read books on weekends.","sentence_cn":"我的英语老师是王老师。\n她和蔼又有趣。\n我喜欢英语课。\n我周末看书。","note":"描写老师和周末生活短文"}
        ]
    },
    "5年级下册": {
        "words": [
            {"en":"eat breakfast","phonetic":"/iːt ˈbrekfəst/","cn":"吃早饭","sentence_en":"I eat breakfast at 7:00.","sentence_cn":"我七点钟吃早饭。","note":"动词短语，eat+三餐"},
            {"en":"have class","phonetic":"/hæv klɑːs/","cn":"上课","sentence_en":"We have class at eight.","sentence_cn":"我们八点钟上课。","note":"have class上课固定短语"},
            {"en":"play sports","phonetic":"/pleɪ spɔːts/","cn":"进行体育运动","sentence_en":"I play sports after school.","sentence_cn":"放学后我做运动。","note":"play sports做体育运动"},
            {"en":"spring","phonetic":"/sprɪŋ/","cn":"春天","sentence_en":"I like spring best.","sentence_cn":"我最喜欢春天。","note":"四季单词首字母小写"},
            {"en":"summer","phonetic":"/ˈsʌmə(r)/","cn":"夏天","sentence_en":"I can swim in summer.","sentence_cn":"夏天我可以游泳。","note":"夏天可以游泳"},
            {"en":"autumn","phonetic":"/ˈɔːtəm/","cn":"秋天","sentence_en":"Autumn is golden.","sentence_cn":"秋天一片金黄。","note":"美式也写fall"},
            {"en":"winter","phonetic":"/ˈwɪntə(r)/","cn":"冬天","sentence_en":"It’s cold in winter.","sentence_cn":"冬天天气很冷。","note":"冬天会下雪"},
            {"en":"January","phonetic":"/ˈdʒænjuəri/","cn":"一月","sentence_en":"New year is in January.","sentence_cn":"新年在一月。","note":"月份首字母大写，介词in+月份"},
            {"en":"February","phonetic":"/ˈfebruəri/","cn":"二月","sentence_en":"Winter is in Jan and Feb.","sentence_cn":"冬天在一月二月。","note":"月份缩写Feb."}
        ],
        "sentences": [
            {"en":"When do you get up? I get up at 7 o'clock.","phonetic":"","cn":"你什么时候起床？我七点起床。","sentence_en":"When do you get up? I get up at 7 o'clock.","sentence_cn":"你什么时候起床？我七点起床。","note":"询问做事情的时间用when"},
            {"en":"Which season do you like best?","phonetic":"","cn":"你最喜欢哪个季节？","sentence_en":"Which season do you like best?","sentence_cn":"你最喜欢哪个季节？","note":"like best最喜欢，询问四季"}
        ],
        "articles": [
            {"en":"I like spring best.\nThe trees turn green.\nI can fly kites.\nSpring is beautiful.","phonetic":"","cn":"我最喜欢春天。\n树木变绿。\n我可以放风筝。\n春天很美。","sentence_en":"I like spring best.\nThe trees turn green.\nI can fly kites.\nSpring is beautiful.","sentence_cn":"我最喜欢春天。\n树木变绿。\n我可以放风筝。\n春天很美。","note":"描写春天景色阅读小短文"}
        ]
    },
    "6年级上册": {
        "words": [
            {"en":"science museum","phonetic":"/ˈsaɪəns mjuˈziːəm/","cn":"科学博物馆","sentence_en":"Where is the science museum?","sentence_cn":"科学博物馆在哪里？","note":"问路单元核心地点名词"},
            {"en":"post office","phonetic":"/pəʊst ˈɒfɪs/","cn":"邮局","sentence_en":"Turn left at the post office.","sentence_cn":"在邮局左转。","note":"寄信寄快递的地方"},
            {"en":"bookstore","phonetic":"/ˈbʊkstɔː(r)/","cn":"书店","sentence_en":"There is a bookstore near here.","sentence_cn":"这附近有一家书店。","note":"book+store合成词"},
            {"en":"hospital","phonetic":"/ˈhɒspɪtl/","cn":"医院","sentence_en":"Turn right at the hospital.","sentence_cn":"在医院右转。","note":"看病就医的地点"},
            {"en":"turn left","phonetic":"/tɜːn left/","cn":"左转","sentence_en":"Turn left at the crossing.","sentence_cn":"在十字路口左转。","note":"指路短语turn left左转"},
            {"en":"turn right","phonetic":"/tɜːn raɪt/","cn":"右转","sentence_en":"Turn right, you can see it.","sentence_cn":"右转，你就能看见它。","note":"指路turn right右转"},
            {"en":"go straight","phonetic":"/ɡəʊ streɪt/","cn":"直走","sentence_en":"Go straight for five minutes.","sentence_cn":"直走五分钟。","note":"go straight一直向前走"},
            {"en":"subway","phonetic":"/ˈsʌbweɪ/","cn":"地铁","sentence_en":"I go by subway.","sentence_cn":"我坐地铁出行。","note":"交通方式by+交通工具不加s"},
            {"en":"hobby","phonetic":"/ˈhɒbi/","cn":"爱好","sentence_en":"What are your hobbies?","sentence_cn":"你的爱好是什么？","note":"hobby复数hobbies，y变i加es"}
        ],
        "sentences": [
            {"en":"How can I get there? Turn right at the hospital.","phonetic":"","cn":"我怎么到那里？在医院右转。","sentence_en":"How can I get there? Turn right at the hospital.","sentence_cn":"我怎么到那里？在医院右转。","note":"问路指路核心句型 How can I get there?"},
            {"en":"What are you going to do tomorrow?","phonetic":"","cn":"你明天打算做什么？","sentence_en":"What are you going to do tomorrow?","sentence_cn":"你明天打算做什么？","note":"be going to表示将来计划打算"}
        ],
        "articles": [
            {"en":"I want to go to the bookstore.\nIt's next to the hospital.\nI will buy a storybook.\nI will go by bus.","phonetic":"","cn":"我想去书店。\n书店在医院旁边。\n我要买一本故事书。\n我坐公交车过去。","sentence_en":"I want to go to the bookstore.\nIt's next to the hospital.\nI will buy a storybook.\nI will go by bus.","sentence_cn":"我想去书店。\n书店在医院旁边。\n我要买一本故事书。\n我坐公交车过去。","note":"问路出行主题阅读"}
        ]
    },
    "6年级下册": {
        "words": [
            {"en":"younger","phonetic":"/ˈjʌŋɡə(r)/","cn":"更年轻的","sentence_en":"You are younger than me.","sentence_cn":"你比我更年轻。","note":"young比较级‑er，than比"},
            {"en":"older","phonetic":"/ˈəʊldə(r)/","cn":"更年长的","sentence_en":"He is older than his brother.","sentence_cn":"他比他弟弟年纪更大。","note":"old比较级older"},
            {"en":"taller","phonetic":"/ˈtɔːlə(r)/","cn":"更高的","sentence_en":"Tom is taller than John.","sentence_cn":"汤姆比约翰个子高。","note":"tall比较级taller"},
            {"en":"shorter","phonetic":"/ˈʃɔːtə(r)/","cn":"更矮的；更短的","sentence_en":"I’m shorter than you.","sentence_cn":"我比你个子矮。","note":"short比较级，两层含义"},
            {"en":"thinner","phonetic":"/ˈθɪnə(r)/","cn":"更瘦的","sentence_en":"She is thinner than me.","sentence_cn":"她比我瘦。","note":"thin双写n+er变比较级"},
            {"en":"heavier","phonetic":"/ˈheviə(r)/","cn":"更重的","sentence_en":"The box is heavier.","sentence_cn":"这个盒子更重。","note":"heavy变y为i+er"},
            {"en":"dinosaur","phonetic":"/ˈdaɪnəsɔː(r)/","cn":"恐龙","sentence_en":"Look at that dinosaur.","sentence_cn":"看那只恐龙。","note":"远古动物名词"},
            {"en":"metre","phonetic":"/ˈmiːtə(r)/","cn":"米","sentence_en":"I’m 1.65 metres.","sentence_cn":"我身高1.65米。","note":"长度单位metre，超过1用复数metres"},
            {"en":"kilogram","phonetic":"/ˈkɪləɡræm/","cn":"千克；公斤","sentence_en":"I’m 45 kilograms.","sentence_cn":"我体重45公斤。","note":"重量单位kilogram"}
        ],
        "sentences": [
            {"en":"How tall are you? I'm 1.6 metres.","phonetic":"","cn":"你多高？我1.6米。","sentence_en":"How tall are you? I'm 1.6 metres.","sentence_cn":"你多高？我1.6米。","note":"询问身高重点句型 How tall are you?"},
            {"en":"What did you do last weekend?","phonetic":"","cn":"上周末你做了什么？","sentence_en":"What did you do last weekend?","sentence_cn":"上周末你做了什么？","note":"一般过去时，询问过去发生事情"}
        ],
        "articles": [
            {"en":"Last weekend I stayed at home.\nI cleaned my room.\nI read a storybook.\nI had a happy weekend.","phonetic":"","cn":"上周末我待在家里。\n我打扫了房间。\n我读了一本故事书。\n我度过了愉快的周末。","sentence_en":"Last weekend I stayed at home.\nI cleaned my room.\nI read a storybook.\nI had a happy weekend.","sentence_cn":"上周末我待在家里。\n我打扫了房间。\n我读了一本故事书。\n我度过了愉快的周末。","note":"一般过去时短文，全部动词过去式"}
        ]
    }
}
store = None  # 在 App.build 中按应用私有目录初始化
sm = ScreenManager()
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=12, spacing=12)
        with layout.canvas.before:
            Color(*BG_COLOR)
            self.rect = Rectangle(size=layout.size, pos=layout.pos)
        def update_rect(instance, value):
            self.rect.pos = instance.pos
            self.rect.size = instance.size
        layout.bind(pos=update_rect, size=update_rect)
        self.add_widget(layout)
        self.title_label = Label(text="程君瑞同学英语学习【人教PEP完整版】", font_name=FONT_NAME, font_size=BASE_FONT+4, color=TEXT_COLOR, size_hint_y=0.11)
        layout.add_widget(self.title_label)
        # 动态字号调节按钮
        font_ctrl_layout = GridLayout(cols=2,size_hint_y=0.07,spacing=6)
        btn_font_plus = Button(text="字体 +", font_name=FONT_NAME, font_size=FONT_BUTTON)
        btn_font_minus = Button(text="字体 -", font_name=FONT_NAME, font_size=FONT_BUTTON)
        btn_font_plus.bind(on_press=self.font_inc)
        btn_font_minus.bind(on_press=self.font_dec)
        font_ctrl_layout.add_widget(btn_font_plus)
        font_ctrl_layout.add_widget(btn_font_minus)
        layout.add_widget(font_ctrl_layout)
        grade_layout = GridLayout(cols=4, size_hint_y=0.14, spacing=8)
        self.grade_btn_dict = {}
        grade_list = ["3年级上册","3年级下册","4年级上册","4年级下册","5年级上册","5年级下册","6年级上册","6年级下册"]
        for grade in grade_list:
            btn = Button(text=grade, font_name=FONT_NAME, font_size=FONT_BUTTON, background_color=[0.2,0.6,0.8,1])
            btn.bind(on_press=self.select_grade)
            self.grade_btn_dict[btn] = grade
            grade_layout.add_widget(btn)
        layout.add_widget(grade_layout)
        mode_layout = GridLayout(cols=2, size_hint_y=0.13, spacing=8)
        btn_word = Button(text="单词练习", font_name=FONT_NAME, font_size=FONT_BUTTON)
        btn_sentence = Button(text="句子短文", font_name=FONT_NAME, font_size=FONT_BUTTON)
        btn_word.bind(on_press=self.goto_word)
        btn_sentence.bind(on_press=self.goto_sentence)
        mode_layout.add_widget(btn_word)
        mode_layout.add_widget(btn_sentence)
        layout.add_widget(mode_layout)
        func_layout = GridLayout(cols=3, size_hint_y=0.13, spacing=8)
        btn_fav = Button(text="收藏单词", font_name=FONT_NAME, font_size=FONT_BUTTON)
        btn_wrong = Button(text="错题本", font_name=FONT_NAME, font_size=FONT_BUTTON)
        btn_stat = Button(text="学习统计", font_name=FONT_NAME, font_size=FONT_BUTTON)
        btn_fav.bind(on_press=self.goto_fav)
        btn_wrong.bind(on_press=self.goto_wrong)
        btn_stat.bind(on_press=self.goto_stat)
        func_layout.add_widget(btn_fav)
        func_layout.add_widget(btn_wrong)
        func_layout.add_widget(btn_stat)
        layout.add_widget(func_layout)
        extra_layout = GridLayout(cols=2, size_hint_y=0.11, spacing=8)
        btn_wrong_train = Button(text="错题专项训练", font_name=FONT_NAME, font_size=FONT_BUTTON)
        btn_reset = Button(text="重置全部学习数据", font_name=FONT_NAME, font_size=FONT_BUTTON,background_color=[0.9,0.2,0.2,1])
        btn_wrong_train.bind(on_press=self.goto_wrong_train)
        btn_reset.bind(on_press=self.reset_all_data)
        extra_layout.add_widget(btn_wrong_train)
        extra_layout.add_widget(btn_reset)
        layout.add_widget(extra_layout)
        self.selected_grade = None
    def font_inc(self,inst):
        global BASE_FONT
        BASE_FONT +=4
        self.refresh_all_font()
    def font_dec(self,inst):
        global BASE_FONT
        BASE_FONT -=4
        if BASE_FONT <22:
            BASE_FONT=22
        self.refresh_all_font()
    def refresh_all_font(self):
        word_screen = sm.get_screen("word")
        word_screen.refresh_font()
    def select_grade(self, instance):
        self.selected_grade = self.grade_btn_dict[instance]
        instance.background_color = [0,0.7,0,1]
    def goto_word(self, instance):
        if not self.selected_grade:
            return
        word_screen = sm.get_screen("word")
        word_screen.load_grade(self.selected_grade, "word")
        sm.current = "word"
    def goto_sentence(self, instance):
        if not self.selected_grade:
            return
        sentence_screen = sm.get_screen("word")
        sentence_screen.load_grade(self.selected_grade, "sentence")
        sm.current = "word"
    def goto_wrong_train(self,instance):
        word_screen = sm.get_screen("word")
        word_screen.load_wrong_only()
        sm.current = "word"
    def goto_fav(self, instance):
        fav_screen = sm.get_screen("fav")
        fav_screen.load_data()
        sm.current = "fav"
    def goto_wrong(self, instance):
        wrong_screen = sm.get_screen("wrong")
        wrong_screen.load_data()
        sm.current = "wrong"
    def goto_stat(self, instance):
        stat_screen = sm.get_screen("stat")
        stat_screen.load_stat()
        sm.current = "stat"
    def reset_all_data(self,inst):
        store.delete("stat")
        store.delete("fav")
        store.delete("wrong")
        store.delete("mastered")
class WordScreen(Screen):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.item_list = []
        self.current_item = None
        self.item_type = "word"
        self.grade = ""
        self.tts_speed = 1.0
        self.is_wrong_only = False
        self.random_mode = True
        self.mask_mode = 0
        self.second_count = 0
        self.auto_speak_next = False  #标记：朗读过后下一题自动朗读
        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        with layout.canvas.before:
            Color(*BG_COLOR)
            self.rect = Rectangle(size=layout.size, pos=layout.pos)
        def update_rect(instance, value):
            self.rect.pos = instance.pos
            self.rect.size = instance.size
        layout.bind(pos=update_rect, size=update_rect)
        self.add_widget(layout)
        self.info_label = Label(text="用时：0秒", font_name=FONT_NAME, font_size=BASE_FONT*0.7, size_hint_y=0.06, color=TIME_RED_COLOR)
        layout.add_widget(self.info_label)
        self.question_label = Label(text="请选择年级后开始练习", font_name=FONT_NAME, font_size=BASE_FONT+4, color=TEXT_COLOR, size_hint_y=0.14, markup=True)
        layout.add_widget(self.question_label)
        self.note_label = Label(text="◆知识点：", font_name=FONT_NAME, font_size=BASE_FONT*0.65, color=[0.1,0.1,0.1,1], size_hint_y=0.09, markup=True)
        layout.add_widget(self.note_label)
        self.sentence_label = Label(text="◆课本例句：", font_name=FONT_NAME, font_size=BASE_FONT*0.65, color=[0,0,0,1], size_hint_y=0.10, markup=True)
        layout.add_widget(self.sentence_label)
        self.result_label = Label(text="", font_name=FONT_NAME, font_size=BASE_FONT*0.85, size_hint_y=0.10, markup=True)
        layout.add_widget(self.result_label)

        # --- 把输入框移到下方，和按钮接平，放到所有按钮前面 ---
        btn_layout = GridLayout(cols=4, size_hint_y=0.095, spacing=4)
        btn_read = Button(text="朗读", font_name=FONT_NAME, font_size=FONT_BUTTON)
        btn_submit = Button(text="提交答案", font_name=FONT_NAME, font_size=FONT_BUTTON)
        btn_next = Button(text="下一题", font_name=FONT_NAME, font_size=FONT_BUTTON)
        btn_master = Button(text="已掌握", font_name=FONT_NAME, font_size=FONT_BUTTON,background_color=[0,0.7,0,1])
        btn_read.bind(on_press=self.read_aloud)
        btn_submit.bind(on_press=self.check_answer)
        btn_next.bind(on_press=self.next_item)
        btn_master.bind(on_press=self.mark_mastered)
        btn_layout.add_widget(btn_read)
        btn_layout.add_widget(btn_submit)
        btn_layout.add_widget(btn_next)
        btn_layout.add_widget(btn_master)
        layout.add_widget(btn_layout)

        btn_layout2 = GridLayout(cols=5, size_hint_y=0.095, spacing=4)
        btn_trans_e2c = Button(text="英译汉", font_name=FONT_NAME, font_size=FONT_BUTTON)
        btn_trans_c2e = Button(text="汉译英", font_name=FONT_NAME, font_size=FONT_BUTTON)
        btn_fav = Button(text="收藏", font_name=FONT_NAME, font_size=FONT_BUTTON)
        btn_speed_slow = Button(text="语速切换", font_name=FONT_NAME, font_size=FONT_BUTTON)
        btn_rand_order = Button(text="随机/顺序", font_name=FONT_NAME, font_size=FONT_BUTTON)
        btn_trans_e2c.bind(on_press=lambda x:self.set_mode("e2c"))
        btn_trans_c2e.bind(on_press=lambda x:self.set_mode("c2e"))
        btn_fav.bind(on_press=self.add_fav)
        btn_speed_slow.bind(on_press=self.toggle_speed)
        btn_rand_order.bind(on_press=self.toggle_random)
        btn_layout2.add_widget(btn_trans_e2c)
        btn_layout2.add_widget(btn_trans_c2e)
        btn_layout2.add_widget(btn_fav)
        btn_layout2.add_widget(btn_speed_slow)
        btn_layout2.add_widget(btn_rand_order)
        layout.add_widget(btn_layout2)

        btn_layout3 = GridLayout(cols=4, size_hint_y=0.09, spacing=4)
        btn_mask0 = Button(text="全部显示", font_name=FONT_NAME, font_size=FONT_BUTTON)
        btn_mask1 = Button(text="遮英文", font_name=FONT_NAME, font_size=FONT_BUTTON)
        btn_mask2 = Button(text="遮中文", font_name=FONT_NAME, font_size=FONT_BUTTON)
        btn_dictation = Button(text="听写模式", font_name=FONT_NAME, font_size=FONT_BUTTON,background_color=[0.8,0.3,0.8,1])
        btn_mask0.bind(on_press=lambda x:self.set_mask(0))
        btn_mask1.bind(on_press=lambda x:self.set_mask(1))
        btn_mask2.bind(on_press=lambda x:self.set_mask(2))
        btn_dictation.bind(on_press=lambda x:self.set_mask(3))
        btn_layout3.add_widget(btn_mask0)
        btn_layout3.add_widget(btn_mask1)
        btn_layout3.add_widget(btn_mask2)
        btn_layout3.add_widget(btn_dictation)
        layout.add_widget(btn_layout3)

        #输入答案框移到此，和按钮接平
        self.answer_input = TextInput(hint_text="在这里输入答案", font_name=FONT_NAME, font_size=BASE_FONT*0.8, size_hint_y=0.09, multiline=True)
        layout.add_widget(self.answer_input)

        btn_back = Button(text="返回主页", font_name=FONT_NAME, font_size=FONT_BUTTON, size_hint_y=0.065)
        btn_back.bind(on_press=lambda x: setattr(sm, "current", "main"))
        layout.add_widget(btn_back)

        self.mode = "e2c"
    def refresh_font(self):
        self.info_label.font_size = BASE_FONT*0.7
        self.question_label.font_size = BASE_FONT+4
        self.note_label.font_size = BASE_FONT*0.65
        self.sentence_label.font_size = BASE_FONT*0.65
        self.answer_input.font_size = BASE_FONT*0.8
        self.result_label.font_size = BASE_FONT*0.85
    def set_mask(self,mode):
        self.mask_mode = mode
        self.next_item(None)
    def toggle_random(self,inst):
        self.random_mode = not self.random_mode
        inst.text="随机" if self.random_mode else "顺序"
    def toggle_speed(self, inst):
        if self.tts_speed ==1.0:
            self.tts_speed =0.6
            inst.text="正常语速"
        else:
            self.tts_speed =1.0
            inst.text="慢速"
    def load_grade(self, grade, item_type):
        self.is_wrong_only=False
        self.grade = grade
        self.item_type = item_type
        self.auto_speak_next = False
        if item_type == "word":
            self.item_list = word_data[grade]["words"]
        elif item_type == "sentence":
            self.item_list = word_data[grade]["sentences"] + word_data[grade]["articles"]
        if self.random_mode:
            random.shuffle(self.item_list)
        self.next_item(None)
    def load_wrong_only(self):
        self.is_wrong_only=True
        self.item_list=[]
        self.auto_speak_next = False
        if store.exists("wrong"):
            self.item_list = store.get("wrong")["items"]
        if self.random_mode:
            random.shuffle(self.item_list)
        self.next_item(None)
    def set_mode(self, mode):
        self.mode = mode
        self.next_item(None)
    def mark_mastered(self,inst):
        if not self.current_item:
            return
        if not store.exists("mastered"):
            store.put("mastered",items=[])
        mlist = store.get("mastered")["items"]
        if self.current_item not in mlist:
            mlist.append(self.current_item)
            store.put("mastered",items=mlist)
            self.result_label.text="[color=#00aa00]已标记为掌握[/color]"
    def next_item(self, instance):
        if len(self.item_list) <= 0:
            self.question_label.text = "[color=#000000]本部分练习完成！[/color]"
            self.note_label.text = "◆知识点："
            self.sentence_label.text = "◆课本例句："
            self.result_label.text = ""
            self.info_label.text="用时：0秒"
            self.second_count=0
            self.auto_speak_next = False
            return
        self.second_count +=1
        self.info_label.text=f"用时：{self.second_count} 秒"
        if self.random_mode:
            self.current_item = random.choice(self.item_list)
        else:
            self.current_item = self.item_list.pop(0)
        self.answer_input.text = ""
        self.result_label.text = ""
        note_txt = self.current_item.get("note","无知识点注解")
        phonetic_txt = self.current_item.get("phonetic","")
        sen_en = self.current_item.get("sentence_en","")
        sen_cn = self.current_item.get("sentence_cn","")
        self.note_label.text = f"◆知识点：{note_txt}"
        self.sentence_label.text = f"◆例句:{sen_en}  [color={RED_CN}]{sen_cn}[/color]"
        if self.mask_mode ==3:
            self.question_label.text="[color=#000000]听声音默写，点击朗读按钮播放[/color]"
        else:
            if self.mode == "e2c":
                show_en = self.current_item["en"]
                if phonetic_txt:
                    show_en = show_en +"  "+phonetic_txt
                if self.mask_mode ==1:
                    show_en="????????????????"
                self.question_label.text = f"[color=#0000bb]{show_en}[/color]"
            else:
                raw_cn = self.current_item["cn"]
                if self.mask_mode ==2:
                    disp_cn="????????????"
                else:
                    disp_cn=f"[color={RED_CN}]{raw_cn}[/color]"
                self.question_label.text = disp_cn
        # 如果之前点过朗读，下一题自动朗读
        if self.auto_speak_next:
            self.read_aloud(None)
    def check_answer(self, instance):
        if self.current_item is None:
            return
        user_ans = self.answer_input.text.strip()
        if self.mode == "e2c":
            right_ans = self.current_item["cn"]
        else:
            right_ans = self.current_item["en"]
        if not store.exists("stat"):
            store.put("stat", total=0, right=0)
        stat = store.get("stat")
        stat["total"] += 1
        if user_ans.lower() == right_ans.lower():
            self.result_label.text = f"[color=#00aa00]回答正确！[/color] [color={RED_CN}]{right_ans}[/color]"
            stat["right"] +=1
        else:
            self.result_label.text = f"[color=#dd0000]答案错误！[/color] 正确：[color={RED_CN}]{right_ans}[/color]"
            if not store.exists("wrong"):
                store.put("wrong", items=[])
            wrong_list = store.get("wrong")["items"]
            if self.current_item not in wrong_list:
                wrong_list.append(self.current_item)
            store.put("wrong", items=wrong_list)
        store.put("stat", total=stat["total"], right=stat["right"])
    def read_aloud(self, instance):
        if self.current_item is None:
            return
        ok = speak_en(self.current_item["en"], speed=self.tts_speed)
        if not ok:
            self.result_label.text = "[color=#dd7700]朗读暂不可用，请检查系统语音包[/color]"
        else:
            #点朗读成功，标记下一题自动朗读
            self.auto_speak_next = True
    def add_fav(self, instance):
        if not self.current_item:
            return
        if not store.exists("fav"):
            store.put("fav", items=[])
        fav_list = store.get("fav")["items"]
        if self.current_item not in fav_list:
            fav_list.append(self.current_item)
            store.put("fav", items=fav_list)
            self.result_label.text = "[color=#ddaa00]已收藏！[/color]"
class FavScreen(Screen):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=10, spacing=8)
        with layout.canvas.before:
            Color(*BG_COLOR)
            self.rect = Rectangle(size=layout.size, pos=layout.pos)
        def update_rect(instance, value):
            self.rect.pos = instance.pos
            self.rect.size = instance.size
        layout.bind(pos=update_rect, size=update_rect)
        self.add_widget(layout)
        title = Label(text="收藏单词句子", font_name=FONT_NAME, font_size=BASE_FONT+4, color=TEXT_COLOR, size_hint_y=0.07)
        layout.add_widget(title)
        top_btn_layout=GridLayout(cols=2,size_hint_y=0.07,spacing=6)
        btn_export = Button(text="导出文本预览",font_name=FONT_NAME,font_size=FONT_BUTTON)
        btn_clear_all = Button(text="清空全部收藏",font_name=FONT_NAME,font_size=FONT_BUTTON,background_color=[0.9,0.2,0.2,1])
        btn_export.bind(on_press=self.export_text)
        btn_clear_all.bind(on_press=self.clear_all_fav)
        top_btn_layout.add_widget(btn_export)
        top_btn_layout.add_widget(btn_clear_all)
        layout.add_widget(top_btn_layout)
        scroll = ScrollView()
        self.scroll_layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=10)
        self.scroll_layout.bind(minimum_height=self.scroll_layout.setter("height"))
        scroll.add_widget(self.scroll_layout)
        layout.add_widget(scroll)
        btn_back = Button(text="返回主页", font_name=FONT_NAME, font_size=FONT_BUTTON, size_hint_y=0.07)
        btn_back.bind(on_press=lambda x: setattr(sm, "current", "main"))
        layout.add_widget(btn_back)
        self.export_popup=None
    def export_text(self,inst):
        txt_out=""
        if store.exists("fav"):
            for it in store.get("fav")["items"]:
                note = it.get("note","无注解")
                ph = it.get("phonetic","")
                txt_out += f"{it['en']} {ph}｜{it['cn']} 【知识点：{note}】\n"
        box=BoxLayout(orientation="vertical",padding=10,spacing=8)
        lab=Label(text=txt_out if txt_out else "暂无收藏",font_name=FONT_NAME,font_size=BASE_FONT*0.65)
        btn_close=Button(text="关闭",size_hint_y=0.14,font_name=FONT_NAME,font_size=FONT_BUTTON)
        btn_close.bind(on_press=lambda x:self.export_popup.dismiss())
        box.add_widget(lab)
        box.add_widget(btn_close)
        self.export_popup=Popup(title="收藏文本预览",content=box,size_hint=(0.92,0.8))
        self.export_popup.open()
    def clear_all_fav(self,inst):
        store.delete("fav")
        self.load_data()
    def load_data(self):
        self.scroll_layout.clear_widgets()
        if store.exists("fav"):
            fav_items = store.get("fav")["items"]
            for item in fav_items:
                note = item.get("note","无注解")
                ph = item.get("phonetic","")
                row = BoxLayout(orientation="vertical", spacing=3,size_hint_y=None,height=100)
                row_top = BoxLayout(spacing=8,size_hint_y=None,height=50)
                disp_text = f"[color=#0000bb]{item['en']} {ph}[/color]｜[color={RED_CN}]{item['cn']}[/color]"
                txt = Label(text=disp_text, font_name=FONT_NAME, font_size=BASE_FONT*0.75, markup=True)
                btn_spk = Button(text="读",font_name=FONT_NAME,font_size=FONT_BUTTON,size_hint_x=0.16)
                btn_spk.bind(on_press=lambda x,it=item: speak_en(it["en"]))
                row_top.add_widget(txt)
                row_top.add_widget(btn_spk)
                note_lab = Label(text=f"◆{note}", font_name=FONT_NAME, font_size=BASE_FONT*0.58, color=[0.15,0.15,0.15,1])
                row.add_widget(row_top)
                row.add_widget(note_lab)
                self.scroll_layout.add_widget(row)
class WrongScreen(Screen):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=10, spacing=8)
        with layout.canvas.before:
            Color(*BG_COLOR)
            self.rect = Rectangle(size=layout.size, pos=layout.pos)
        def update_rect(instance, value):
            self.rect.pos = instance.pos
            self.rect.size = instance.size
        layout.bind(pos=update_rect, size=update_rect)
        self.add_widget(layout)
        title = Label(text="错题本", font_name=FONT_NAME, font_size=BASE_FONT+4, color=TEXT_COLOR, size_hint_y=0.07)
        layout.add_widget(title)
        top_btn_layout=GridLayout(cols=2,size_hint_y=0.07,spacing=6)
        btn_export_wrong = Button(text="导出错题预览",font_name=FONT_NAME,font_size=FONT_BUTTON)
        btn_clear_wrong = Button(text="清空全部错题",font_name=FONT_NAME,font_size=FONT_BUTTON,background_color=[0.9,0.2,0.2,1])
        btn_export_wrong.bind(on_press=self.export_wrong_text)
        btn_clear_wrong.bind(on_press=self.clear_all_wrong)
        top_btn_layout.add_widget(btn_export_wrong)
        top_btn_layout.add_widget(btn_clear_wrong)
        layout.add_widget(top_btn_layout)
        scroll = ScrollView()
        self.scroll_layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=10)
        self.scroll_layout.bind(minimum_height=self.scroll_layout.setter("height"))
        scroll.add_widget(self.scroll_layout)
        layout.add_widget(scroll)
        btn_back = Button(text="返回主页", font_name=FONT_NAME, font_size=FONT_BUTTON, size_hint_y=0.07)
        btn_back.bind(on_press=lambda x: setattr(sm, "current", "main"))
        layout.add_widget(btn_back)
        self.popup_wrong=None
    def export_wrong_text(self,inst):
        txt_out=""
        if store.exists("wrong"):
            for it in store.get("wrong")["items"]:
                note = it.get("note","无注解")
                ph = it.get("phonetic","")
                txt_out += f"{it['en']} {ph}｜{it['cn']} 【知识点：{note}】\n"
        box=BoxLayout(orientation="vertical",padding=10,spacing=8)
        lab=Label(text=txt_out if txt_out else "暂无错题",font_name=FONT_NAME,font_size=BASE_FONT*0.65)
        btn_close=Button(text="关闭",size_hint_y=0.14,font_name=FONT_NAME,font_size=FONT_BUTTON)
        btn_close.bind(on_press=lambda x:self.popup_wrong.dismiss())
        box.add_widget(lab)
        box.add_widget(btn_close)
        self.popup_wrong=Popup(title="错题文本预览",content=box,size_hint=(0.92,0.8))
        self.popup_wrong.open()
    def clear_all_wrong(self,inst):
        store.delete("wrong")
        self.load_data()
    def load_data(self):
        self.scroll_layout.clear_widgets()
        if store.exists("wrong"):
            wrong_items = store.get("wrong")["items"]
            for item in wrong_items:
                note = item.get("note","无注解")
                ph = item.get("phonetic","")
                row = BoxLayout(orientation="vertical", spacing=3,size_hint_y=None,height=100)
                row_top = BoxLayout(spacing=8,size_hint_y=None,height=50)
                disp_text = f"[color=#0000bb]{item['en']} {ph}[/color]｜[color={RED_CN}]{item['cn']}[/color]"
                txt = Label(text=disp_text, font_name=FONT_NAME, font_size=BASE_FONT*0.75, markup=True)
                btn_spk = Button(text="读",font_name=FONT_NAME,font_size=FONT_BUTTON,size_hint_x=0.16)
                btn_spk.bind(on_press=lambda x,it=item: speak_en(it["en"]))
                row_top.add_widget(txt)
                row_top.add_widget(btn_spk)
                note_lab = Label(text=f"◆{note}", font_name=FONT_NAME, font_size=BASE_FONT*0.58, color=[0.15,0.15,0.15,1])
                row.add_widget(row_top)
                row.add_widget(note_lab)
                self.scroll_layout.add_widget(row)
class StatScreen(Screen):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=16, spacing=16)
        with layout.canvas.before:
            Color(*BG_COLOR)
            self.rect = Rectangle(size=layout.size, pos=layout.pos)
        def update_rect(instance, value):
            self.rect.pos = instance.pos
            self.rect.size = instance.size
        layout.bind(pos=update_rect, size=update_rect)
        self.add_widget(layout)
        self.stat_label = Label(text="学习统计", font_name=FONT_NAME, font_size=BASE_FONT+4, color=TEXT_COLOR, markup=True)
        layout.add_widget(self.stat_label)
        btn_back = Button(text="返回主页", font_name=FONT_NAME, font_size=FONT_BUTTON, size_hint_y=0.07)
        btn_back.bind(on_press=lambda x: setattr(sm, "current", "main"))
        layout.add_widget(btn_back)
    def load_stat(self):
        total=0
        right=0
        fav_num=0
        wrong_num=0
        master_num=0
        if store.exists("stat"):
            data = store.get("stat")
            total = data["total"]
            right = data["right"]
        if store.exists("fav"):
            fav_num=len(store.get("fav")["items"])
        if store.exists("wrong"):
            wrong_num=len(store.get("wrong")["items"])
        if store.exists("mastered"):
            master_num=len(store.get("mastered")["items"])
        if total == 0:
            rate = 0
        else:
            rate = round(right / total *100,1)
        self.stat_label.text = (
f"学习统计\n"
f"总答题：{total}题\n"
f"答对：{right}题\n"
f"正确率：{rate}%\n"
f"收藏数量：{fav_num}\n"
f"错题数量：{wrong_num}\n"
f"已掌握单词：{master_num}"
        )
sm.add_widget(MainScreen(name="main"))
sm.add_widget(WordScreen(name="word"))
sm.add_widget(FavScreen(name="fav"))
sm.add_widget(WrongScreen(name="wrong"))
sm.add_widget(StatScreen(name="stat"))
class EnglishStudyApp(App):
    def build(self):
        global store
        # 存档放在应用私有目录：APK 内也保证可写，调试/打包行为一致
        try:
            store = JsonStore(os.path.join(self.user_data_dir, "english_data.json"))
        except Exception as e:
            print("初始化存档失败，回退到工作目录", e)
            store = JsonStore("english_data.json")
        Window.clearcolor = BG_COLOR
        return sm
    def on_stop(self):
        if platform == "android" and tts is not None:
            try:
                tts.shutdown()
            except Exception:
                pass
if __name__ == "__main__":
     EnglishStudyApp().run()
