use bcrypt::{hash, verify, DEFAULT_COST};
use chrono::{Duration, Utc};
use jsonwebtoken::{decode, encode, Algorithm, DecodingKey, EncodingKey, Header, TokenData, Validation};
use uuid::Uuid;
use crate::config::Settings;
use crate::error::{AppError, AppResult};

pub fn hash_password(password: &str) -> AppResult<String> {
    hash(password, DEFAULT_COST).map_err(AppError::from)
}

pub fn verify_password(password: &str, hashed: &str) -> AppResult<bool> {
    verify(password, hashed).map_err(AppError::from)
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Claims {
    pub sub: String,
    pub exp: i64,
    pub iat: i64,
}

pub fn create_access_token(subject: Uuid, settings: &Settings) -> AppResult<String> {
    let now = Utc::now();
    let expire = now + Duration::minutes(settings.access_token_expire_minutes);

    let claims = Claims {
        sub: subject.to_string(),
        exp: expire.timestamp(),
        iat: now.timestamp(),
    };

    encode(
        &Header::default(),
        &claims,
        &EncodingKey::from_secret(settings.secret_key.as_bytes()),
    )
    .map_err(AppError::from)
}

pub fn decode_access_token(token: &str, settings: &Settings) -> AppResult<TokenData<Claims>> {
    let mut validation = Validation::new(Algorithm::HS256);
    validation.validate_exp = true;
    validation.leeway = 0;
    validation.required_spec_claims = ["exp", "iat"].into_iter().map(|s| s.to_string()).collect();

    decode::<Claims>(
        token,
        &DecodingKey::from_secret(settings.secret_key.as_bytes()),
        &validation,
    )
    .map_err(AppError::from)
}