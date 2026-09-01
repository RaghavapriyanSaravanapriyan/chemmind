use config::{Config, ConfigError, Environment, File};
use serde::Deserialize;
use std::path::PathBuf;

#[derive(Debug, Deserialize, Clone)]
pub struct Settings {
    pub project_name: String,
    pub api_v1_str: String,
    pub environment: String,

    // Security & JWT
    pub secret_key: String,
    pub algorithm: String,
    pub access_token_expire_minutes: i64,

    // CORS
    pub backend_cors_origins: Vec<String>,

    // File Storage Settings
    pub storage_dir: PathBuf,
    pub max_upload_size_mb: i64,
    pub allowed_extensions: Vec<String>,

    // Workspace Quota Limits
    pub default_workspace_doc_limit: i64,
    pub default_workspace_storage_mb: i64,
    pub default_workspace_ai_request_limit: i64,

    // Database Configuration
    pub database_url: String,

    // AI Configuration
    pub ollama_base_url: String,
    pub default_llm_model: String,
    pub default_embedding_model: String,

    // Logging
    pub log_level: String,
}

impl Settings {
    pub fn new() -> Result<Self, ConfigError> {
        let config = Config::builder()
            .add_source(File::with_name(".env").required(false))
            .add_source(Environment::with_prefix("CHEMMIND"))
            .build()?;

        config.try_deserialize()
    }

    pub fn database_url(&self) -> &str {
        &self.database_url
    }
}

impl Default for Settings {
    fn default() -> Self {
        Self {
            project_name: "ChemMind Backend API".to_string(),
            api_v1_str: "/api/v1".to_string(),
            environment: "development".to_string(),
            secret_key: "chemmind_super_secret_key_change_in_production_32bytes_min".to_string(),
            algorithm: "HS256".to_string(),
            access_token_expire_minutes: 60 * 24 * 30,
            backend_cors_origins: vec!["http://localhost:3000".to_string(), "http://127.0.0.1:3000".to_string()],
            storage_dir: PathBuf::from("uploads"),
            max_upload_size_mb: 50,
            allowed_extensions: vec![
                ".pdf".to_string(),
                ".txt".to_string(),
                ".md".to_string(),
                ".csv".to_string(),
                ".tex".to_string(),
                ".tsv".to_string(),
                ".json".to_string(),
                ".rst".to_string(),
                ".org".to_string(),
                ".log".to_string(),
            ],
            default_workspace_doc_limit: 50,
            default_workspace_storage_mb: 500,
            default_workspace_ai_request_limit: 200,
            database_url: "postgresql://postgres:postgres_password@localhost:5432/chemmind_db".to_string(),
            ollama_base_url: "http://localhost:11434".to_string(),
            default_llm_model: "llama3".to_string(),
            default_embedding_model: "nomic-embed-text".to_string(),
            log_level: "INFO".to_string(),
        }
    }
}

pub fn get_settings() -> Settings {
    Settings::new().unwrap_or_default()
}