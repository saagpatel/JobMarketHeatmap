use std::sync::Mutex;

use tauri::Manager;
use tauri_plugin_shell::process::CommandChild;
use tauri_plugin_shell::ShellExt;
use tauri_plugin_store::StoreExt;

struct SidecarState(Mutex<Option<CommandChild>>);

#[tauri::command]
async fn set_credentials(
    app: tauri::AppHandle,
    app_id: String,
    app_key: String,
) -> Result<(), String> {
    let store = app.store("credentials.json").map_err(|e| e.to_string())?;
    store.set("adzuna_app_id", serde_json::json!(app_id));
    store.set("adzuna_app_key", serde_json::json!(app_key));
    Ok(())
}

#[tauri::command]
async fn get_credentials(app: tauri::AppHandle) -> Result<Option<(String, String)>, String> {
    let store = app.store("credentials.json").map_err(|e| e.to_string())?;
    let app_id = store
        .get("adzuna_app_id")
        .and_then(|v| v.as_str().map(String::from));
    let app_key = store
        .get("adzuna_app_key")
        .and_then(|v| v.as_str().map(String::from));
    match (app_id, app_key) {
        (Some(id), Some(key)) => Ok(Some((id, key))),
        _ => Ok(None),
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_store::Builder::default().build())
        .manage(SidecarState(Mutex::new(None)))
        .invoke_handler(tauri::generate_handler![set_credentials, get_credentials])
        .setup(|app| {
            match app.shell().sidecar("main") {
                Ok(sidecar_command) => {
                    match sidecar_command.spawn() {
                        Ok((_rx, child)) => {
                            println!("[sidecar] Spawned successfully");
                            let state = app.state::<SidecarState>();
                            *state.0.lock().unwrap() = Some(child);
                        }
                        Err(e) => {
                            println!(
                                "[sidecar] DEV MODE: Could not spawn sidecar ({}). Run uvicorn manually.",
                                e
                            );
                        }
                    }
                }
                Err(e) => {
                    println!(
                        "[sidecar] DEV MODE: Sidecar binary not found ({}). Run uvicorn manually.",
                        e
                    );
                }
            }
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app_handle, event| {
            if let tauri::RunEvent::Exit = event {
                let state = app_handle.state::<SidecarState>();
                let child = state.0.lock().unwrap().take();
                if let Some(child) = child {
                    // Attempt graceful shutdown via HTTP before killing
                    let _ = std::process::Command::new("curl")
                        .args([
                            "-s",
                            "-X",
                            "POST",
                            "http://127.0.0.1:8008/shutdown",
                            "--max-time",
                            "2",
                        ])
                        .output();

                    let _ = child.kill();
                    println!("[sidecar] Killed on app exit");
                }
            }
        });
}
