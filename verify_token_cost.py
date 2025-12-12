from app.services.llm.token_service import token_service

def verify_token_costs():
    print("--- Verifying Token Cost Estimation ---")
    
    test_cases = [
        ("azure/genailab-maas-gpt-35-turbo", 1000, 1000),
        ("azure/genailab-maas-gpt-4o", 1000, 1000),
        ("azure_ai/genailab-maas-Llama-3.3-70B-Instruct", 1000, 1000),
        ("azure_ai/genailab-maas-DeepSeek-R1", 1000, 1000),
        ("unknown-gpt-4-variant", 1000, 1000), # Should fallback to gpt-4o
        ("completely-unknown-model", 1000, 1000) # Should fallback to gpt-3.5-turbo
    ]
    
    for model, input_tokens, output_tokens in test_cases:
        cost = token_service.estimate_cost(input_tokens, output_tokens, model)
        print(f"Model: {model}")
        print(f"  Input: {input_tokens}, Output: {output_tokens}")
        print(f"  Estimated Cost: ${cost:.6f}")
        print("-" * 30)

if __name__ == "__main__":
    verify_token_costs()
