"""Test script to verify OpenAPI schema generation"""
import json
from app.main import app


def test_openapi_generation():
    """Test that OpenAPI schema is generated correctly"""
    # Get the OpenAPI schema
    openapi_schema = app.openapi()
    
    # Verify basic structure
    assert "openapi" in openapi_schema
    assert "info" in openapi_schema
    assert "paths" in openapi_schema
    assert "components" in openapi_schema
    
    # Verify security schemes
    assert "securitySchemes" in openapi_schema["components"]
    assert "BearerAuth" in openapi_schema["components"]["securitySchemes"]
    
    # Verify common schemas
    assert "schemas" in openapi_schema["components"]
    assert "ErrorResponse" in openapi_schema["components"]["schemas"]
    assert "PaginationMetadata" in openapi_schema["components"]["schemas"]
    
    # Verify custom extensions
    assert "x-error-codes" in openapi_schema
    assert "x-role-permissions" in openapi_schema
    assert "x-points-system" in openapi_schema
    
    # Verify API info
    assert openapi_schema["info"]["title"] == "LPanda Meta-Jungle Task & Reward Management Platform"
    assert "description" in openapi_schema["info"]
    
    # Print summary
    print("✓ OpenAPI schema generated successfully")
    print(f"✓ API Title: {openapi_schema['info']['title']}")
    print(f"✓ API Version: {openapi_schema['info']['version']}")
    print(f"✓ Number of paths: {len(openapi_schema['paths'])}")
    print(f"✓ Number of schemas: {len(openapi_schema['components']['schemas'])}")
    print(f"✓ Security schemes: {list(openapi_schema['components']['securitySchemes'].keys())}")
    
    # Save to file for inspection
    with open("backend/openapi_schema.json", "w") as f:
        json.dump(openapi_schema, f, indent=2)
    print("✓ OpenAPI schema saved to backend/openapi_schema.json")
    
    return True


if __name__ == "__main__":
    try:
        test_openapi_generation()
        print("\n✅ All OpenAPI documentation tests passed!")
    except Exception as e:
        print(f"\n❌ OpenAPI documentation test failed: {e}")
        raise
