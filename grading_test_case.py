from answer import collect_class_forest

input_one = "./loki-sn-bot/lokisnbot"
input_two = "./Commpy/Commpy"
intput_three = "./NekoGram/NekoGram"
input_four = "./portfolio-management-project/models"

def test_one():
    expected = {'NetworkContext': {'TelegramContext': {}, 'DiscordContext': {}}, 'Network': {'TelegramNetwork': {}, 'DiscordNetwork': {}}}
    student_answer = collect_class_forest(input_one)
    assert expected == student_answer
    print(student_answer)

def test_two():
    expected = {'_FlatChannel': {'SISOFlatChannel': {}, 'MIMOFlatChannel': {}}, 'Modem': {'PSKModem': {}, 'QAMModem': {}}, 'ModemTestcase': {'TestModulateHardDemodulate': {}, 'TestEs': {}}, 'MIMOTestCase': {'TestMIMODefaultArgs': {}, 'TestMIMOFading': {}, 'TestMIMOSpectular': {}, 'TestMIMONoiseGeneration': {}, 'TestMIMOTypeCheck': {}, 'TestMIMOShapes': {}, 'TestMIMOkFactor': {}}, '_Interleaver': {'RandInterlv': {}}}
    student_answer = collect_class_forest(input_two)
    assert expected == student_answer
    print(student_answer)

def test_three():
    expected = {'BaseNeko': {'Neko': {}}, 'BaseStorage': {'SQLiteStorage': {'KittySQLiteStorage': {}}, 'PGStorage': {'KittyPGStorage': {}}, 'MySQLStorage': {'KittyMySQLStorage': {}}}, 'BaseProcessor': {'JSONProcessor': {}, 'YAMLProcessor': {}}}
    student_answer = collect_class_forest(intput_three)
    assert expected == student_answer
    print(student_answer)

def test_four():
    expected = {'DBObject': {'DBTransaction': {}, 'DBPosition': {}, 'DBPieChartData': {}, 'DBUser': {}}}
    student_answer = collect_class_forest(input_four)
    assert expected == student_answer
    print(student_answer)


