use chemmind_backend::auth::{hash_password, verify_password, create_access_token, decode_access_token, Claims};
use chemmind_backend::config::Settings;
use uuid::Uuid;

#[test]
fn test_password_hashing() {
    let password = "test_password_123";
    let hashed = hash_password(password).unwrap();
    
    assert_ne!(hashed, password);
    assert!(verify_password(password, &hashed).unwrap());
    assert!(!verify_password("wrong_password", &hashed).unwrap());
}

#[test]
fn test_jwt_token_creation_and_validation() {
    let settings = Settings::default();
    let user_id = Uuid::new_v4();
    
    let token = create_access_token(user_id, &settings).unwrap();
    let token_data = decode_access_token(&token, &settings).unwrap();
    
    let claims = token_data.claims;
    assert_eq!(claims.sub, user_id.to_string());
    assert!(claims.exp > claims.iat);
}

#[test]
fn test_expired_token_rejected() {
    let mut settings = Settings::default();
    settings.access_token_expire_minutes = -1; // Expired
    
    let user_id = Uuid::new_v4();
    let token = create_access_token(user_id, &settings).unwrap();
    
    let result = decode_access_token(&token, &settings);
    assert!(result.is_err());
}