# utils/token_generator.py
import secrets
import base64


def generate_api_key(length: int = 32) -> str:
    """
    Generate a secure random API key
    
    Args:
        length: Number of random bytes (default 32 = 256 bits)
    
    Returns:
        Base64 encoded API key string
    """
    random_bytes = secrets.token_bytes(length)
    api_key = base64.urlsafe_b64encode(random_bytes).decode('utf-8')
    return api_key


def generate_multiple_keys(count: int = 3, length: int = 32) -> dict:
    """
    Generate multiple API keys with different permissions
    
    Args:
        count: Number of keys to generate
        length: Byte length of each key
    
    Returns:
        Dictionary with key names and generated keys
    """
    keys = {}
    permission_types = ["email", "sms", "auth", "admin", "general"]
    
    for i in range(count):
        permission = permission_types[i % len(permission_types)]
        key_name = f"API_KEY_{permission.upper()}_{i+1}"
        keys[key_name] = {
            "key": generate_api_key(length),
            "permissions": [permission]
        }
    
    return keys


if __name__ == "__main__":
    print("=" * 80)
    print("API KEY GENERATOR")
    print("=" * 80)
    print("\n🔑 Single API Key:")
    print(f"   {generate_api_key()}")
    
    print("\n" + "=" * 80)
    print("🔐 Multiple API Keys with Permissions:")
    print("=" * 80)
    
    keys = generate_multiple_keys(5)
    
    for key_name, key_data in keys.items():
        print(f"\n{key_name}:")
        print(f"  Key:         {key_data['key']}")
        print(f"  Permissions: {', '.join(key_data['permissions'])}")
    
    print("\n" + "=" * 80)
    print("📝 Add these to your .env file:")
    print("=" * 80)
    for key_name, key_data in keys.items():
        print(f'{key_name}="{key_data["key"]}"')
    
    print("\n" + "=" * 80)
    print("📋 Add these to your API_KEYS dictionary in api_key_auth.py:")
    print("=" * 80)
    print("API_KEYS = {")
    for key_name, key_data in keys.items():
        permissions_str = ', '.join([f'"{p}"' for p in key_data['permissions']])
        print(f'    os.getenv("{key_name}", "{key_data["key"]}"): [{permissions_str}],')
    print("}")
    
    print("\n✅ Done! Keep these keys secure!\n")