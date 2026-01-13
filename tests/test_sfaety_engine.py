from safety_engine import evaluate_reading

def test_h2s_warning():
    result = evaluate_reading("S1", "H2S", 12)
    assert result[0] == "WARNING"

def test_h2s_critical():
    result = evaluate_reading("S1", "H2S", 25)
    assert result[0] == "CRITICAL"

def test_h2s_safe():
    result = evaluate_reading("S1", "H2S", 3)
    assert result is None

def test_o2_critical_low():
    result = evaluate_reading("S2", "O2", 15.5)
    assert result[0] == "CRITICAL"

def test_o2_safe():
    result = evaluate_reading("S2", "O2", 20.9)
    assert result is None
