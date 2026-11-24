"""One-time generator for data/songs.yaml, performers.yaml, programs.yaml, captions.yaml.

The YAML files are the source of truth afterwards; edit them, not this script.
Song rows: title | yomi | id | aliases(;) | season(;) | themes(;)
Empty yomi -> drafted with pykakasi and marked reviewed: false.
"""
import re
import sys
from pathlib import Path

import pykakasi
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline.jp import normalize, to_hiragana  # noqa: E402

SONGS = """
夜桜お七|よざくらおしち|yozakura-oshichi|お七|春|桜;恋
また君に恋してる|またきみにこいしてる|mata-kimi-ni-koishiteru|まだ君に恋してる;また君に恋して||恋
ほろ酔い満月|ほろよいまんげつ|horoyoi-mangetsu|ほろよい満月|秋|月;酒
あばれ太鼓|あばれだいこ|abare-daiko|||祭
遠い昔の恋の歌|とおいむかしのこいのうた|tooi-mukashi-no-koi-no-uta|||恋
再会酒場|さいかいさかば|saikai-sakaba|再会酒場(セリフ入り)||酒
ひらり|ひらり|hirari|||
能登はいらんかいね|のとはいらんかいね|noto-wa-iirankaine|||故郷
浪花魂|なにわだましい|naniwa-damashii|||故郷
男の火祭り|おとこのひまつり|otoko-no-himatsuri|||祭
祝い酒|いわいざけ|iwaizake|||祝;酒
火の国の女|ひのくにのおんな|hi-no-kuni-no-onna|||恋
想い出づくり|おもいでづくり|omoide-zukuri|||恋
心の糸|こころのいと|kokoro-no-ito|||
天城越え|あまぎごえ|amagigoe|||恋
雪の花|ゆきのはな|yuki-no-hana||冬|雪
アジアの海賊|あじあのかいぞく|asia-no-kaizoku|||
人生いろいろ|じんせいいろいろ|jinsei-iroiro|||
しあわせ十色|しあわせといろ|shiawase-toiro|||祝
雪深深|ゆきしんしん|yuki-shinshin||冬|雪
こころ酒|こころざけ|kokorozake|||酒
風に立つ|かぜにたつ|kaze-ni-tatsu|風に立つ！||
羅生門|らしょうもん|rashomon|||
岸壁の母|がんぺきのはは|ganpeki-no-haha|||母
男の情話|おとこのじょうわ|otoko-no-jowa|||
もう一度逢いたい|もういちどあいたい|mou-ichido-aitai|||恋
うりずんの頃|うりずんのころ|urizun-no-koro||春|
百年桜|ひゃくねんざくら|hyakunen-zakura||春|桜
ひまわりの約束|ひまわりのやくそく|himawari-no-yakusoku||夏|
ロンリー・チャップリン|ろんりーちゃっぷりん|lonely-chaplin|ロンリーチャップリン||恋
恋の予感|こいのよかん|koi-no-yokan|||恋
いとしのエリー|いとしのえりー|itoshi-no-ellie|||恋
好きになった人|すきになったひと|suki-ni-natta-hito|||恋
恋は火の舞剣の舞|こいはひのまいけんのまい|koi-wa-hi-no-mai|恋は火の舞 剣の舞||祭
千本桜|せんぼんざくら|senbonzakura||春|桜
お祭りマンボ|おまつりまんぼ|omatsuri-mambo||夏|祭
ミ・アモーレ|みあもーれ|mi-amore|||恋
レーザービーム|れーざーびーむ|laser-beam|Laser Beam||
酒と泪と男と女|さけとなみだとおとことおんな|sake-to-namida|||酒
街の灯り|まちのあかり|machi-no-akari|||
ずっとあなたが好きでした|ずっとあなたがすきでした|zutto-anata-ga|||恋
女がひとり|おんながひとり|onna-ga-hitori|||
酔中花|すいちゅうか|suichuka|||酒
風うた|かぜうた|kaze-uta|||
海猫|うみねこ|umineko|||
夜明けのうた|よあけのうた|yoake-no-uta|||
花はただ咲く|はなはたださく|hana-wa-tada-saku|||
明治一代女|めいじいちだいおんな|meiji-ichidai-onna|||
暖簾|のれん|noren|||
ふりむかないで|ふりむかないで|furimukanaide|||
栞のテーマ|しおりのてーま|shiori-no-theme|||
熊野路へ|くまのじへ|kumanoji-e|||故郷
もしも明日が…|もしもあしたが|moshimo-ashita-ga|もしも明日が||
別れの予感|わかれのよかん|wakare-no-yokan|||恋
一度だけなら|いちどだけなら|ichido-dake-nara|||恋
からたちの小径|からたちのこみち|karatachi-no-komichi|||
夏をあきらめて|なつをあきらめて|natsu-wo-akiramete||夏|
Angel|Angel|angel|||
裸の心|はだかのこころ|hadaka-no-kokoro|||恋
誰もいない海|だれもいないうみ|daremo-inai-umi||夏|
東京だョおっ母さん|とうきょうだよおっかさん|tokyo-da-yo-okkasan|||母
居酒屋|いざかや|izakaya|||酒
巡ループ|めぐるーぷ|meguloop|||
逢いたくて逢いたくて|あいたくてあいたくて|aitakute|||恋
満月|まんげつ|mangetsu||秋|月
瀬戸の花嫁|せとのはなよめ|seto-no-hanayome|||祝;故郷
おんな港町|おんなみなとまち|onna-minatomachi|||
My Heart Belongs to Daddy|My Heart Belongs to Daddy|my-heart-belongs-to-daddy|My Heart's Belongs||
花は咲く|はなはさく|hana-wa-saku|||
花のワルツ|はなのわるつ|hana-no-waltz|||
大阪で生まれた女|おおさかでうまれたおんな|osaka-de-umareta-onna|||故郷
男と女のラブゲーム|おとことおんなのらぶげーむ|love-game|||
3年目の浮気|さんねんめのうわき|sannenme-no-uwaki|||
会いたい|あいたい|aitai|||恋
ブッダのように私は死んだ|ぶっだのようにわたしはしんだ|buddha-no-you-ni|||
恋をするなら|こいをするなら|koi-wo-suru-nara|||恋
orion|orion|orion|||
シングルベッド|しんぐるべっど|single-bed|||
うなじ魅せ|うなじみせ|unaji-mise|||
浮雲ふたつ|うきぐもふたつ|ukigumo-futatsu|||
湖畔の宿|こはんのやど|kohan-no-yado|||
帰ろかな|かえろかな|kaero-kana|||故郷
花束|はなたば|hanataba|||
飾りじゃないのよ涙は|かざりじゃないのよなみだは|kazari-janai-noyo|||
雨の御堂筋|あめのみどうすじ|ame-no-midosuji|||
SWEET MEMORIES|SWEET MEMORIES|sweet-memories|||
銀座の恋の物語|ぎんざのこいのものがたり|ginza-no-koi|||恋
テネシー・ワルツ|てねしーわるつ|tennessee-waltz|||
喝采|かっさい|kassai|||
かもめの街|かもめのまち|kamome-no-machi|||
竜二|りゅうじ|ryuji|||
ほろ酔いダンス|ほろよいだんす|horoyoi-dance|||酒
TATTOO|TATTOO|tattoo|||
朧月夜に死にましょう|おぼろづきよにしにましょう|oborozukiyo|||月
L-O-V-E|L-O-V-E|love|||恋
恋花||koibana|||恋
夜間飛行|やかんひこう|yakan-hiko|||
ブルー・ライト・ヨコハマ|ぶるーらいとよこはま|blue-light-yokohama|||
花筐|はながたみ|hanagatami|||
淋しがり|さみしがり|samishigari|||
それが大事|それがだいじ|sore-ga-daiji|||
いつもそばにいるよ|いつもそばにいるよ|itsumo-soba-ni|||
わかって下さい|わかってください|wakatte-kudasai|||
チキチキバンバン|ちきちきばんばん|chiki-chiki-bang-bang|||
男惚れ|おとこぼれ|otoko-bore|||
Dancing Queen|Dancing Queen|dancing-queen|||
じょんから女節|じょんからおんなぶし|jonkara-onnabushi|||故郷
丸の内サディスティック|まるのうちさでぃすてぃっく|marunouchi-sadistic|丸ノ内サディスティック||
南部大黒舞|なんぶだいこくまい|nanbu-daikokumai|||祭;故郷
秋田大黒舞|あきただいこくまい|akita-daikokumai|||祭;故郷
ふたり道|ふたりみち|futari-michi|||
夜桜お七殺人事件|よざくらおしちさつじんじけん|yozakura-oshichi-satsujin|||
ふるさと|ふるさと|furusato|||故郷
花水仙|はなすいせん|hana-suisen||冬|
東尋坊|とうじんぼう|tojinbo|||
冗談じゃない|じょうだんじゃない|jodan-janai|||
恋しくて|こいしくて|koishikute|||恋
女|おんな|onna|||
ここから|ここから|kokokara|||
夫婦善哉|めおとぜんざい|meoto-zenzai|||
薔薇ホテル|ばらほてる|bara-hotel|||
ジェラシー|じぇらしー|jealousy|||
おかあさん|おかあさん|okaasan|||母
四季の歌|しきのうた|shiki-no-uta|||
昭和枯れすすき|しょうわかれすすき|showa-karesusuki||秋|
オリビアを聴きながら|おりびあをききながら|olivia|||
ひばりの佐渡情話|ひばりのさどじょうわ|hibari-no-sado-jowa|ひぱりの佐渡情話||故郷
紅い糸|あかいいと|akai-ito|||恋
黄色いさくらんぼ|きいろいさくらんぼ|kiiroi-sakuranbo|黃色いさくらんぼ||
気まぐれ道中|きまぐれどうちゅう|kimagure-dochu|||
世界中の誰よりきっと|せかいじゅうのだれよりきっと|sekaiju-no-dare-yori|||恋
伊勢佐木町ブルース|いせざきちょうぶるーす|isezakicho-blues|||
香港香港|ほんこんほんこん|hongkong-hongkong|||
Vagare|Vagare|vagare|||
鴎という名の酒場|かもめというなのさかば|kamome-to-iu-na|||酒
ひなげしの花|ひなげしのはな|hinageshi-no-hana||夏|
望郷|ぼうきょう|bokyo|||故郷
大阪ラプソディー|おおさからぷそでぃー|osaka-rhapsody|||故郷
人生の並木路|じんせいのなみきみち|jinsei-no-namikimichi|||
恋雨〜KOISAME〜|こいさめ|koisame|恋雨||恋
エレクトロ・ワールド|えれくとろわーるど|electro-world|Electro world||
チョコレイト・ディスコ|ちょこれいとでぃすこ|chocolate-disco|Chocolate disco||
FLASH|FLASH|flash|Flash||
黒田節|くろだぶし|kurodabushi|||酒
無法松の一生|むほうまつのいっしょう|muhomatsu|||
夫婦春秋|めおとしゅんじゅう|meoto-shunju|||
ロック・アンド・ロール・ミュージック|ろっくあんどろーるみゅーじっく|rock-and-roll-music|||
ヘルプ！|へるぷ|help|||
アンド・アイ・ラヴ・ハー|あんどあいらゔはー|and-i-love-her|||
夏ざかりほの字組|なつざかりほのじぐみ|natsuzakari-honojigumi|夏ざかり ほの字組|夏|
和歌山ブルース|わかやまぶるーす|wakayama-blues|||故郷
生命のブルース|いのちのぶるーす|inochi-no-blues|||
うそよ今夜も|うそよこんやも|usoyo-konya-mo|||
帰れない二人|かえれないふたり|kaerenai-futari|||
時代|じだい|jidai|||
港のヨーコヨコハマヨコスカ|みなとのようこよこはまよこすか|minato-no-yoko|港のヨーコ・ヨコハマ・ヨコスカ||
禁区|きんく|kinku|||
想いびと|おもいびと|omoibito|||恋
誕生|たんじょう|tanjo|||祝
サクラ、散ル|さくらちる|sakura-chiru|||桜
故郷へ…|ふるさとへ|furusato-e|故郷へ||故郷
勝手にシンドバッド|かってにしんどばっど|katte-ni-sinbad||夏|
私鉄沿線|してつえんせん|shitetsu-ensen|||
愛して愛して愛しちゃったのよ|あいしてあいしてあいしちゃったのよ|aishite-aishite|||恋
命の花よ|いのちのはなよ|inochi-no-hana-yo|||
乙女座宮|おとめざぐう|otomeza-gu|乙女座 宮||
祇園小唄|ぎおんこうた|gion-kouta|||故郷
恋するフォーチュンクッキー|こいするふぉーちゅんくっきー|fortune-cookie|恋するフォーチューンクッキー||
「いちご白書」をもう一度|いちごはくしょをもういちど|ichigo-hakusho|||
真夏の夜の夢|まなつのよるのゆめ|manatsu-no-yoru||夏|
ダンシング・ヒーロー|だんしんぐひーろー|dancing-hero|||
秋田音頭|あきたおんど|akita-ondo|秋田音頭-AKITA ONDO||祭;故郷
素肌|すはだ|suhada|||
ふたりの愛ランド|ふたりのあいらんど|futari-no-island||夏|
月亮代表我的心（永遠の月）|げつりょうだいひょうがてきしん|yue-liang|月亮代表我的心||月
勝手にしやがれ|かってにしやがれ|katte-ni-shiyagare|||
あや子のお国自慢だよ〜|あやこのおくにじまんだよ|ayako-no-okuni-jiman|あや子のお国自慢だよ||故郷
がんばろな東北|がんばろなとうほく|ganbarona-tohoku|||故郷
また逢う日まで|またあうひまで|mata-au-hi-made|||
渚にまつわるエトセトラ|なぎさにまつわるえとせとら|nagisa-etcetera||夏|
小さな鐘の音〜ラ・カンパネラ〜|ちいさなかねのね|chiisana-kane-no-ne|小さな鐘の音〜う・カンパネラ〜;小さな鐘の音||
梅川忠兵衛|うめかわちゅうべえ|umekawa-chubei|梅川忠兵衛(歌謡浪曲)||
曼珠沙華|まんじゅしゃげ|manjushage||秋|
北の海明け|きたのうみあけ|kita-no-umiake||冬|
二輪草|にりんそう|nirinso|||
誰よりも君を愛す|だれよりもきみをあいす|dare-yori-mo-kimi-wo|||恋
木曾の恋唄|きそのこいうた|kiso-no-koiuta|||恋;故郷
しなやかに歌って|しなやかにうたって|shinayaka-ni-utatte|||
さよなら|さよなら|sayonara|||
時の過ぎゆくままに|ときのすぎゆくままに|toki-no-sugiyuku|||
浪花恋しぐれ|なにわこいしぐれ|naniwa-koishigure|||恋;故郷
夜明けのブルース|よあけのぶるーす|yoake-no-blues|||
北の宿から|きたのやどから|kita-no-yado-kara||冬|
金毘羅一段|こんぴらいちだん|konpira-ichidan|||
いい日旅立ち|いいひたびだち|ii-hi-tabidachi|||
二人でお酒を|ふたりでおさけを|futari-de-osake-wo|||酒
恋のしずく|こいのしずく|koi-no-shizuku|||恋
愛するってこわい|あいするってこわい|aisuru-tte-kowai|||恋
一恵|ひとえ|hitoe|||
むらさき雨情|むらさきうじょう|murasaki-ujo|||
恋の町札幌|こいのまちさっぽろ|koi-no-machi-sapporo|||恋;故郷
雨夜酒||amayozake|||酒
さだめ川|さだめがわ|sadamegawa|||
あの日にかえりたい|あのひにかえりたい|ano-hi-ni-kaeritai|||
桜の如く|さくらのごとく|sakura-no-gotoku||春|桜
風立ちぬ|かぜたちぬ|kaze-tachinu||秋|
こしの都|こしのみやこ|koshi-no-miyako|||故郷
おかえりがおまもり|おかえりがおまもり|okaeri-ga-omamori|||
特攻の母〜ホタル〜|とっこうのはは|tokko-no-haha|特攻の母||母
津軽海峡・冬景色|つがるかいきょうふゆげしき|tsugaru-kaikyo||冬|雪
この世の花|このよのはな|konoyo-no-hana|||
逢いたいなァあの人に|あいたいなあのひとに|aitaina-ano-hito-ni|||
思い出さん今日は|おもいでさんこんにちは|omoidesan-konnichiwa|||
さよならはダンスの後に|さよならはだんすのあとに|sayonara-wa-dance|||
ちあきなおみ名曲メドレー|ちあきなおみめいきょくめどれー|chiaki-naomi-medley|||
喧嘩安兵衛 前伝|けんかやすべえぜんでん|kenka-yasubei|||
夢ん中|ゆめんなか|yumen-naka|||
蛍の提灯|ほたるのちょうちん|hotaru-no-chochin||夏|
雪燃えて|ゆきもえて|yuki-moete||冬|雪
京のにわか雨|きょうのにわかあめ|kyo-no-niwakaame|||
二人は若い|ふたりはわかい|futari-wa-wakai|||
1812 Overture|1812 Overture|1812-overture|||
ラストダンスは私に|らすとだんすはわたしに|last-dance|||
人生しみじみ|じんせいしみじみ|jinsei-shimijimi|||
白いスーツのテーマ|しろいすーつのてーま|white-suit-theme|||
愛のさざなみ|あいのさざなみ|ai-no-sazanami|||恋
雪荒野|ゆきこうや|yuki-koya||冬|雪
恋蛍〜瀧の白糸より〜|こいぼたる|koibotaru|恋蛍||恋
風雪流れ旅|ふうせつながれたび|fusetsu-nagaretabi||冬|雪
故郷|ふるさと|furusato-shoka|||故郷
この道|このみち|kono-michi|||
毬と殿様|まりととのさま|mari-to-tonosama|||
見上げてごらん夜の星を|みあげてごらんよるのほしを|miagete-goran|||
翼をください|つばさをください|tsubasa-wo-kudasai|||
恋愛サーキュレーション|れんあいさーきゅれーしょん|renai-circulation|||
矢切の渡し|やぎりのわたし|yagiri-no-watashi|||
東京ナイト・クラブ|とうきょうないとくらぶ|tokyo-night-club|||
流氷恋唄|りゅうひょうこいうた|ryuhyo-koiuta||冬|雪
上を向いて歩こう|うえをむいてあるこう|ue-wo-muite|||
大阪で生まれた女|おおさかでうまれたおんな|osaka-de-umareta-onna|||故郷
爛漫!花づくし句会|らんまんはなづくしくかい|ranman-hanazukushi||春|
""".strip()

PERFORMERS = """坂本冬美 藤あや子 五木ひろし 伍代夏子 内田有紀 八代亜紀 二葉百合子 市川由紀乃 香西かおり 石川さゆり
一路真輝 青山新 原田悠里 大塚宝 吉幾三 川中美幸 長山洋子 三山ひろし 辰巳ゆうと 由紀さおり 田川寿美 天童よしみ
中森明菜 夏川りみ 竹島宏 田原俊彦 Perfume アグネス・チャン 石原詢子 村田英雄 小林幸子 M!LK 西城なつ美 JUJU
福田こうへい 水森かおり 杜このみ 森進一 大月みやこ 神野美伽 南こうせつ 北島三郎 中島美嘉 津吹みゆ 羽山みずき
明石家さんま 山内恵介 千昌夫 鳥羽一郎 一条貫太 岩本公水 丘みどり 松原のぶえ 彩青 小柳ルミ子 細川たかし MIYAVI
コロッケ 大石まどか 桑田佳祐 尾藤イサオ 加藤和樹 ちあきなおみ 水谷千重子 岡田美里 川奈ルミ 秋元順子 平原綾香
水城なつみ 安田祥子 すぎもとまさと キム・ヨンジャ 前川清 山本譲二 中村梅雀 泉ピン子 都はるみ あいみょん 谷村新司
松任谷由実 西田敏行 堀内孝雄 松田聖子 椎名佐千子 ビリー・バンバン 倉木麻衣 クミコ 村方乃々佳 大川栄策 岩崎宏美
坂本冬休み 森山愛子 森口博子 岡千秋 中村美律子 大竹しのぶ 島倉千代子""".split()
UNITS = {"演歌5人娘": [], "演歌三人娘": ["演歌3人娘"], "艶歌四人姫": [], "四人姫": [], "二葉組": [], "あやふゆ": [],
         "出演者全員": [], "ベイビーブー": [], "LE VELVETS": [], "Eric Martin": [], "ゴスペラーズ": ["ゴズぺラーズ"],
         "DAIGO": ["Daigo"], "演歌三人娘＆中森明菜": []}
ALIASES = {"新浜レオン": ["新浜レオ"], "島津亜矢": ["島津亞矢"]}

CAPTIONS = """VTR 出張朝市 輪島朝市 松下IMPホール ご自慢有名人調査 和歌山編 新曲初TV放送 初TVライブ収録 LIVE_CHALLENGE 新曲紹介
早稲田大学大隈記念講堂 草月ホール 上高地帝国ホテル 上高地 清澄庭園 こんなかっこいい人っているんだ 辰野金吾 日本銀行本店本館
テレビ初ライブ かっこいい〜〜 ヨドコウ迎賓館 志摩観光ホテル 帝国ホテル東京 浅草ふくまる旅館 オープニングテーマ 鳥取境港ver.
学士会館 東京女子大学礼拝堂 満月のお七さん〜〜 原宿冬美ちゃん 八代亜紀デビュー50年！名曲だらけの永久保存版！ Tchaikovsky
歌謡浪曲 cut (含talking) talking 森口博子でしょう〜""".split()

PROGRAMS = {
    "人生、歌がある": ["人生歌", "人生歌がある", "人生歌 坂本冬美名場面集＋名曲・名演集！", "人生歌 坂本冬美名場面集+名曲・名演集!"],
    "NHK紅白歌合戦": ["紅白", "紅白歌合戦", "第77回ＮＨＫ紅白歌合戦", "第59回紅白", "第45回紅白"],
    "新BS日本のうた": ["新BS日本のうた", "新BS日本のうた たっぷり静岡", "木曜8時のコンサート、新BS日本のうた"],
    "うたコン": ["うたコン", "うたコン 拡大版スペシャル"],
    "徳光和夫の名曲にっぽん": ["徳光和夫の名曲にっぽん", "徳光和夫の名曲にっぽん 長編ドラマチックSP・後編", "徳光和夫の名曲にっぽん 東北ご当地ソングSP", "徳光リクエスト"],
    "演歌フェス": ["演歌フェス", "演歌フェス2025"],
    "Music Fair": ["Music Fair", "MUSIC FAIR"],
    "徹子の部屋": ["徹子の部屋", "徹子の部屋コンサート"],
    "日本の名曲 人生、歌がある": [],
    "新・美の巨人たち": ["新美の巨人たち"],
    "歌謡コンサート": ["歌謡コンサート", "歌謡コンサート 愛のドラマチック歌謡"],
    "昭和歌謡ベストテンDX": ["昭和歌謡ベストテンDX"],
    "年忘れにっぽんの歌": ["年忘れにっぽんの歌", "第58回年忘れ"],
    "はやウタ": ["はやウタ"],
    "おはよう！僕らの名曲ショー": ["名曲ショー"],
    "八代亜紀 いい歌いい話": ["八代亜紀いい歌いい話"],
    "演歌の花道": ["演歌の花道"],
    "昭和歌謡パレード": ["昭和歌謡パレード"],
    "歌謡プレミアム": ["歌謡プレミアム"],
    "BS日本・こころの歌": [],
    "木曜8時のコンサート": ["木曜8時のコンサート"],
    "ボクらの時代": ["ボクらの時代"],
    "ニッポンの歌ヂカラ": ["ニッポンの歌ヂカラ"],
    "FNS鬼レンチャン歌謡祭": ["FNS鬼レンチャン歌謡祭"],
    "ファミリーヒストリー": ["ファミリーヒストリー"],
    "ふたりのビッグショー": ["ふたりのビッグショー"],
    "人生最高レストラン": ["人生最高レストラン"],
    "ラヴィット！": ["ラヴィット"],
    "ヒルナンデス！": ["ヒルナンデス"],
    "めざましテレビ": ["めざましテレビ"],
    "グッド！モーニング": ["グッド!モーニング", "グッドモーニング"],
    "よ～いドン！": ["よーいドン", "よ〜いドン", "よ~いドン"],
    "じゅん散歩": ["じゅん散歩"],
    "ぴったんこカン・カン": ["ぴったんこカン・カン"],
    "帰れマンデー見っけ隊!!": ["帰れマンデー", "サンド秘境バス旅 帰れマンデー見っけ隊"],
    "月曜から夜ふかし": ["月曜から夜ふかし"],
    "メレンゲの気持ち": ["メレンゲの気持ち"],
    "サタデープラス": ["サタプラ"],
    "洋子の演歌一直線": ["洋子の演歌一直線", "洋子の演歌一直線 六月韓国女子旅"],
    "歌謡ショー": ["木曜夜の歌謡ショー"],
}


def kakasi_yomi(title):
    k = pykakasi.kakasi()
    return "".join(i["hira"] for i in k.convert(title))


def is_kana(s):
    return all("ぁ" <= c <= "ヿ" or c in "・ー！〜…、" for c in s)


def main():
    out, seen = [], set()
    for line in SONGS.splitlines():
        title, yomi, sid, aliases, season, themes = (line.split("|") + [""] * 6)[:6]
        if sid in seen:
            continue
        seen.add(sid)
        reviewed = bool(yomi)
        if not yomi:
            yomi = to_hiragana(title) if is_kana(title) else kakasi_yomi(title)
        out.append({"id": sid, "title": title, "yomi": yomi,
                    "aliases": [a for a in aliases.split(";") if a],
                    "season": [s for s in season.split(";") if s],
                    "themes": [t for t in themes.split(";") if t], "reviewed": reviewed})
    dump = lambda p, o: Path(p).write_text(yaml.safe_dump(o, allow_unicode=True, sort_keys=False, width=200), "utf-8")
    dump("data/songs.yaml", out)
    perf = [{"name": n, "aliases": ALIASES.get(n, []), "unit": False} for n in PERFORMERS]
    perf += [{"name": n, "aliases": ALIASES.get(n, []), "unit": False} for n in ALIASES if n not in PERFORMERS]
    perf += [{"name": n, "aliases": a, "unit": True} for n, a in UNITS.items()]
    dump("data/performers.yaml", perf)
    dump("data/programs.yaml", [{"name": n, "aliases": a} for n, a in PROGRAMS.items()])
    dump("data/captions.yaml", [c.replace("_", " ") for c in CAPTIONS])
    print(len(out), "songs,", len(perf), "performers")


if __name__ == "__main__":
    main()
