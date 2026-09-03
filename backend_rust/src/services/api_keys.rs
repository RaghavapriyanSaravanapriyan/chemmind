use std::collections::HashMap;
use std::sync::{Arc, RwLock};

/// Supported external provider identifiers for BYOK (bring-your-own-key).
pub const SUPPORTED_PROVIDERS: &[&str] = &["openai", "anthropic", "gemini", "openrouter", "groq"];

/// Thread-safe in-memory API key store.
///
/// Keys are held in process memory only (never logged, never returned in full).
/// On restart, keys fall back to environment variables
/// (OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY) when present.
/// For production persistence, back this with an encrypted DB table.
#[derive(Clone, Default)]
pub struct ApiKeyStore {
    inner: Arc<RwLock<HashMap<String, String>>>,
}

impl ApiKeyStore {
    pub fn new() -> Self {
        Self {
            inner: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    fn normalize(provider: &str) -> String {
        provider.trim().to_lowercase()
    }

    pub fn is_supported(provider: &str) -> bool {
        SUPPORTED_PROVIDERS.contains(&Self::normalize(provider).as_str())
    }

    /// Stores a key for a provider. Returns error on unsupported provider or empty key.
    pub fn set(&self, provider: &str, api_key: &str) -> Result<(), String> {
        let p = Self::normalize(provider);
        if !Self::is_supported(&p) {
            return Err(format!(
                "Unsupported provider '{}'. Supported: {}",
                provider,
                SUPPORTED_PROVIDERS.join(", ")
            ));
        }
        let key = api_key.trim().to_string();
        if key.is_empty() {
            return Err("API key must not be empty".to_string());
        }
        if key.len() < 8 {
            return Err("API key looks too short".to_string());
        }
        self.inner
            .write()
            .map_err(|_| "Key store lock poisoned".to_string())?
            .insert(p, key);
        Ok(())
    }

    pub fn delete(&self, provider: &str) -> bool {
        let p = Self::normalize(provider);
        self.inner
            .write()
            .map(|mut m| m.remove(&p).is_some())
            .unwrap_or(false)
    }

    /// Returns true if a key is available via store or environment fallback.
    pub fn has(&self, provider: &str) -> bool {
        self.get(provider).is_some()
    }

    /// Returns the key if present in store, else environment fallback. Never logs the value.
    pub fn get(&self, provider: &str) -> Option<String> {
        let p = Self::normalize(provider);
        if let Ok(map) = self.inner.read() {
            if let Some(v) = map.get(&p) {
                return Some(v.clone());
            }
        }
        // Environment fallback (never logged).
        let env_key = match p.as_str() {
            "openai" | "openrouter" | "groq" => std::env::var("OPENAI_API_KEY").ok(),
            "anthropic" => std::env::var("ANTHROPIC_API_KEY").ok(),
            "gemini" => std::env::var("GEMINI_API_KEY").ok(),
            _ => None,
        };
        env_key.filter(|k| !k.trim().is_empty())
    }

    /// Status without exposing secrets: provider -> { configured, source, last4 }.
    pub fn status(&self) -> HashMap<String, serde_json::Value> {
        let mut out = HashMap::new();
        for prov in SUPPORTED_PROVIDERS {
            let stored_last4 = self
                .inner
                .read()
                .ok()
                .and_then(|m| m.get(*prov).cloned())
                .map(|k| format!("…{}", &k[k.len().saturating_sub(4)..]));
            let (configured, source, last4) = if let Some(l4) = stored_last4 {
                (true, "store", Some(l4))
            } else if self.get(prov).is_some() {
                (true, "env", None)
            } else {
                (false, "none", None)
            };
            out.insert(
                prov.to_string(),
                serde_json::json!({
                    "configured": configured,
                    "source": source,
                    "last4": last4,
                }),
            );
        }
        out
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn stores_and_masks_keys() {
        let store = ApiKeyStore::new();
        assert!(store.set("openai", "sk-test-12345678").is_ok());
        assert!(store.has("openai"));
        assert!(store.set("bogus", "sk-12345678").is_err());
        assert!(store.set("openai", "short").is_err());
        let status = store.status();
        assert_eq!(status["openai"]["configured"], true);
        // Full key never appears in status payload.
        let serialized = serde_json::to_string(&status).unwrap();
        assert!(!serialized.contains("sk-test-12345678"));
        assert!(store.delete("openai"));
        assert!(!store.has("openai") || std::env::var("OPENAI_API_KEY").is_ok());
    }
}
