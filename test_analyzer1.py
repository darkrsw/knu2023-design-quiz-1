from app_analyzer import collect_class_forest

test_input_path = "./src/"

def test_class_forest():
    expected = {
        "First": {
          "Second": {
              "Third": {}
          }
        },
        "A": {
          "B": {},
          "C": {}
        }
    }

    result = collect_class_forest(test_input_path)
    assert expected == result
