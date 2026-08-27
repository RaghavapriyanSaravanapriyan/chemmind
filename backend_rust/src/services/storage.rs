use sha2::{Digest, Sha256};
use std::path::{Path, PathBuf};
use tokio::fs;
use tokio::io::AsyncWriteExt;
use uuid::Uuid;
use crate::config::Settings;
use crate::error::{AppError, AppResult};

pub struct StorageService {
    base_dir: PathBuf,
    max_file_size: u64,
    allowed_extensions: Vec<String>,
}

impl StorageService {
    pub fn new(settings: &Settings) -> Self {
        let base_dir = settings.storage_dir.clone();
        let max_file_size = (settings.max_upload_size_mb as u64) * 1024 * 1024;
        let allowed_extensions = settings.allowed_extensions.clone();

        // Ensure base directory exists
        let base_dir_clone = base_dir.clone();
        tokio::spawn(async move {
            if let Err(e) = fs::create_dir_all(&base_dir_clone).await {
                tracing::error!("Failed to create storage directory: {}", e);
            }
        });

        Self {
            base_dir,
            max_file_size,
            allowed_extensions,
        }
    }

    pub async fn save_upload_file(
        &self,
        workspace_id: Uuid,
        mut file: tokio::fs::File,
        filename: &str,
    ) -> AppResult<(String, String, u64)> {
        // Validate file extension
        let ext = Path::new(filename)
            .extension()
            .and_then(|e| e.to_str())
            .map(|e| format!(".{}", e.to_lowercase()))
            .unwrap_or_else(|| ".pdf".to_string());

        if !self.allowed_extensions.iter().any(|allowed| *allowed == ext) {
            return Err(AppError::BadRequest(format!(
                "Unsupported file format '{}'. Allowed formats: {}",
                ext,
                self.allowed_extensions.join(", ")
            )));
        }

        // Create workspace subdirectory
        let ws_dir = self.base_dir.join(workspace_id.to_string());
        fs::create_dir_all(&ws_dir).await?;

        // Generate unique filename
        let unique_filename = format!("{}{}", Uuid::new_v4(), ext);
        let target_path = ws_dir.join(&unique_filename);

        // Calculate checksum and save file
        let mut hasher = Sha256::new();
        let mut file_size = 0u64;
        let mut buffer = vec![0u8; 1024 * 1024]; // 1MB buffer

        let mut out_file = fs::File::create(&target_path).await?;

        loop {
            let n = file.read(&mut buffer).await?;
            if n == 0 {
                break;
            }
            file_size += n as u64;

            if file_size > self.max_file_size {
                // Clean up partial file
                let _ = fs::remove_file(&target_path).await;
                return Err(AppError::PayloadTooLarge(format!(
                    "File size exceeds maximum allowed size of {}MB",
                    self.max_file_size / (1024 * 1024)
                )));
            }

            hasher.update(&buffer[..n]);
            out_file.write_all(&buffer[..n]).await?;
        }

        out_file.flush().await?;
        drop(out_file);

        let checksum = format!("{:x}", hasher.finalize());
        let storage_path = target_path.to_string_lossy().to_string();

        tracing::info!(
            "Saved file {} ({} bytes) to {}",
            filename,
            file_size,
            storage_path
        );

        Ok((storage_path, checksum, file_size))
    }

    pub fn delete_file(&self, storage_path: &str) -> bool {
        let path = Path::new(storage_path);
        if path.exists() {
            match std::fs::remove_file(path) {
                Ok(_) => {
                    tracing::info!("Deleted file from storage: {}", storage_path);
                    true
                }
                Err(e) => {
                    tracing::warn!("Failed to delete file {}: {}", storage_path, e);
                    false
                }
            }
        } else {
            false
        }
    }

    pub fn get_file_path(&self, storage_path: &str) -> Option<PathBuf> {
        let path = Path::new(storage_path);
        if path.exists() {
            Some(path.to_path_buf())
        } else {
            None
        }
    }
}