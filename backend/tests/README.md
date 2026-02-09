# Backend Tests

This directory contains test scripts for the Salla Autonomous Merchant Operations system.

## Test Files

### `run_test.py`
Main integration test that runs the complete LangGraph workflow with sample data.

**Usage:**
```bash
cd backend
python tests/run_test.py
```

**What it tests:**
- Complete workflow execution (Coordinator → Support → Catalog → Validator → Pricing → Resolver)
- Data loading and processing
- Agent coordination
- Final report generation

---

### `test_validation_pipeline.py`
Dedicated test suite for the Validation Pipeline (Hallucination & Contradiction Detection).

**Usage:**
```bash
cd backend
python tests/test_validation_pipeline.py
```

**What it tests:**

#### Test 1: Hallucination Detection
- Verifies the system catches when the Pricing Agent cites competitor data that doesn't exist
- Injects a fake `competitor_price: $85.00` signal with no corresponding data in `pricing_context`
- Expected: Validator flags it as `HALLUCINATION` and blocks the proposal

#### Test 2: Data Mismatch Detection
- Verifies the system catches when the Pricing Agent cites incorrect competitor prices
- Provides real competitor price ($120) but agent claims different price ($85)
- Expected: Validator flags it as `DATA_MISMATCH` and blocks the proposal

#### Test 3: Contradiction Detection
- Verifies the system catches price increases during negative sentiment
- Proposes price increase while `sentiment_score = -0.5`
- Expected: Validator flags it as `CONTRADICTION` and blocks the proposal

---

### `test_azure_connection.py`
Tests Azure OpenAI API connectivity and configuration.

**Usage:**
```bash
cd backend
python tests/test_azure_connection.py
```

---

### `test_azure_simple.py`
Simple Azure OpenAI integration test.

**Usage:**
```bash
cd backend
python tests/test_azure_simple.py
```

---

### `test_llm.py`
Tests LLM configuration and response handling.

**Usage:**
```bash
cd backend
python tests/test_llm.py
```

---

## Running All Tests

To run the complete test suite:

```bash
cd backend

# Run main integration test
python tests/run_test.py

# Run validation pipeline tests
python tests/test_validation_pipeline.py

# Run Azure connection tests
python tests/test_azure_connection.py
```

## Expected Output

### Successful Validation Pipeline Test Output:
```
======================================================================
VALIDATION PIPELINE TEST SUITE
======================================================================

======================================================================
TEST 1: HALLUCINATION DETECTION
======================================================================

🧪 Running workflow with fake competitor data...

--- 🕵️ Validator Agent: Pipeline Checks ---
🚨 Hallucination detected for prod_001: Claimed context that doesn't exist.
✓ Validation complete. Found 1 flags.

✓ Validation Flags Found: 1
  - HALLUCINATION: Agent cited competitor price $85.0, but no competitor data exists for this product.

✓ Pricing Actions:
  - prod_001: Status=BLOCKED, Note=Blocked: Agent cited competitor price $85.0, but no competitor data exists for this product.

✅ TEST PASSED: Hallucination was detected and blocked!

[... similar output for Tests 2 and 3 ...]

======================================================================
🎉 ALL TESTS PASSED!
======================================================================

The validation pipeline successfully:
  ✓ Detects hallucinated competitor data
  ✓ Catches mismatched data claims
  ✓ Identifies contradictory pricing decisions
```

## Environment Setup

Make sure you have:
1. `.env` file configured with Azure OpenAI credentials
2. Virtual environment activated
3. All dependencies installed: `pip install -r requirements.txt`
4. Sample data in `data/` directory

## Troubleshooting

**Import errors:**
- Make sure you're running tests from the `backend` directory
- Tests automatically add the parent directory to `sys.path`

**Azure API errors:**
- Check your `.env` file has correct credentials
- Verify your Azure OpenAI deployment is active
- Check API quota limits

**Data loading errors:**
- Ensure `data/green_data/` or `data/salla_data/` directories exist
- Verify CSV files are properly formatted
