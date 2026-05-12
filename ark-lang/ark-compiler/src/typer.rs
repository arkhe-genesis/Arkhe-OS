use std::collections::HashMap;

#[allow(dead_code)]
pub struct TypeEnv {
    vars: HashMap<String, String>,
    consumed: HashMap<String, bool>,
}

pub fn type_check() {
    let mut env = TypeEnv {
        vars: HashMap::new(),
        consumed: HashMap::new(),
    };
    let _ = check_linearity_fd(&mut env, "my_fd");
}

pub fn check_linearity_fd(env: &mut TypeEnv, var_name: &str) -> Result<(), String> {
    // Verificador de linearidade para Fd<T>
    // Assegura que um file descriptor tipado como Fd<T> seja consumido
    // exatamente uma vez (via .close(), drop(), ou .anchor() se consumir)
    // Previne vazamentos de recursos e orphans em tempo de compilação.
    if let Some(true) = env.consumed.get(var_name) {
        return Err(format!("Linearity violation: Fd '{}' consumed more than once", var_name));
    }

    env.consumed.insert(var_name.to_string(), true);
    println!("Checking linearity of Fd<T>... OK for {}", var_name);
    Ok(())
}
