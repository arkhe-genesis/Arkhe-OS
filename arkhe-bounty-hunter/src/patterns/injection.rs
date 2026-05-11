// ============================================================================
// ARKHE Bounty Hunter — Injection Pattern Detection
// ============================================================================
// Detects SQL injection, command injection, XSS, LDAP injection, XPath injection,
// and other injection vulnerabilities across all languages.
// ============================================================================

use std::collections::HashMap;
use crate::patterns::{PatternRule, PatternDefinition, PatternStep, SeverityLevel};

/// Register all injection-related vulnerability patterns
pub fn register_injection_patterns(db: &mut crate::patterns::VulnerabilityDatabase) {
    // =====================
    // SQL INJECTION (CWE-89)
    // =====================
    db.register(PatternRule {
        id: "INJ-SQL-001".to_string(),
        cwe_id: "CWE-89".to_string(),
        name: "SQL Injection via String Concatenation".to_string(),
        description: "User input is concatenated directly into a SQL query string \
            without parameterization or proper escaping, allowing an attacker \
            to manipulate the query structure.".to_string(),
        pattern: PatternDefinition::Composite {
            operator: crate::patterns::CompositeOp::And,
            patterns: vec![
                PatternDefinition::AstPattern {
                    node_type: "ExprCall".to_string(),
                    attributes: {
                        let mut attrs = HashMap::new();
                        attrs.insert("function_name".to_string(),
                            "(execute|query|raw|sql|exec_sql|run_query|db_query|prepare_statement)".to_string());
                        attrs
                    },
                    children_pattern: Some(Box::new(PatternDefinition::Composite {
                        operator: crate::patterns::CompositeOp::Or,
                        patterns: vec![
                            // String concatenation with user input
                            PatternDefinition::AstPattern {
                                node_type: "ExprBinary".to_string(),
                                attributes: {
                                    let mut a = HashMap::new();
                                    a.insert("operator".to_string(), "(concat|\\+|format!)".to_string());
                                    a
                                },
                                children_pattern: None,
                            },
                            // f-string / template with variables
                            PatternDefinition::AstPattern {
                                node_type: "ExprTemplate".to_string(),
                                attributes: HashMap::new(),
                                children_pattern: None,
                            },
                        ],
                    })),
                },
            ],
        },
        language_specific: false,
        languages: vec![
            "python".into(), "javascript".into(), "typescript".into(),
            "java".into(), "csharp".into(), "php".into(), "ruby".into(),
            "go".into(), "rust".into(), "c".into(), "cpp".into(),
        ],
        severity_default: SeverityLevel::Critical,
        confidence: 0.95,
        remediation: "Use parameterized queries or prepared statements instead of string concatenation.".to_string(),
        fix: Some("cursor.execute(\"SELECT * FROM users WHERE id = ?\", (user_id,))".to_string()),
        owasp_category: Some("A03:2021-Injection".to_string()),
        examples_vulnerable: vec![
            // Python
            "cursor.execute(\"SELECT * FROM users WHERE id = \" + user_id)".to_string(),
            "cursor.execute(f\"SELECT * FROM users WHERE name = '{name}'\")".to_string(),
            "db.query(\"SELECT * FROM users WHERE id = \" + req.params.id)".to_string(),
            // JavaScript
            "db.query('SELECT * FROM users WHERE id = ' + userId)".to_string(),
            "db.query(`SELECT * FROM users WHERE id = ${userId}`)".to_string(),
            // Java
            "stmt.executeQuery(\"SELECT * FROM users WHERE id = \" + userId)".to_string(),
            // PHP
            "mysqli_query($conn, \"SELECT * FROM users WHERE id = \" . $_GET['id'])".to_string(),
            // Ruby
            "User.where(\"name = '\" + params[:name] + \"'\")".to_string(),
            // Go
            "db.Query(\"SELECT * FROM users WHERE id = \" + userId)".to_string(),
            // Rust
            "query(&format!(\"SELECT * FROM users WHERE id = {}\", user_id))".to_string(),
        ],
        examples_safe: vec![
            "cursor.execute(\"SELECT * FROM users WHERE id = ?\", (user_id,))".to_string(),
            "db.query('SELECT * FROM users WHERE id = ?', [userId])".to_string(),
            "stmt.setString(1, userId); stmt.executeQuery()".to_string(),
            "User.where(id: params[:id])".to_string(), // Rails parameterized
        ],
    });

    db.register(PatternRule {
        id: "INJ-SQL-002".to_string(),
        cwe_id: "CWE-89".to_string(),
        name: "ORM Raw Query Injection".to_string(),
        description: "ORM raw() or similar methods accept raw SQL strings that \
            may include unsanitized user input.".to_string(),
        pattern: PatternDefinition::AstPattern {
            node_type: "ExprCall".to_string(),
            attributes: {
                let mut attrs = HashMap::new();
                attrs.insert("function_name".to_string(),
                    "(raw|raw_sql|native_query|createNativeQuery|\\.raw\\(|\\.filterRaw)".to_string());
                attrs
            },
            children_pattern: None,
        },
        language_specific: false,
        languages: vec![
            "python".into(), "javascript".into(), "typescript".into(),
            "java".into(), "php".into(), "ruby".into(), "go".into(),
        ],
        severity_default: SeverityLevel::Critical,
        confidence: 0.92,
        remediation: "Avoid raw queries. Use the ORM's query builder with parameter binding.".to_string(),
        fix: Some("Model::whereRaw('id = ?', [$userInput])".to_string()),
        owasp_category: Some("A03:2021-Injection".to_string()),
        examples_vulnerable: vec![
            "Model::raw('SELECT * FROM users WHERE id = ' + req.query.id)".to_string(),
            "em.createNativeQuery('SELECT * FROM users WHERE name = \\'' + name + '\\'')".to_string(),
            "User.where(\"name = '#{params[:name]}'\")".to_string(),
        ],
        examples_safe: vec![
            "Model::where('id', $userInput)".to_string(),
            "em.createQuery('SELECT u FROM User u WHERE u.id = :id')->setParameter('id', $id)".to_string(),
        ],
    });

    // =====================
    // COMMAND INJECTION (CWE-78)
    // =====================
    db.register(PatternRule {
        id: "INJ-CMD-001".to_string(),
        cwe_id: "CWE-78".to_string(),
        name: "OS Command Injection".to_string(),
        description: "User input is passed to system shell commands without \
            proper sanitization, allowing arbitrary command execution.".to_string(),
        pattern: PatternDefinition::Composite {
            operator: crate::patterns::CompositeOp::And,
            patterns: vec![
                PatternDefinition::AstPattern {
                    node_type: "ExprCall".to_string(),
                    attributes: {
                        let mut attrs = HashMap::new();
                        attrs.insert("function_name".to_string(),
                            "(exec|execSync|spawn|execSync|system|popen|Process\\.start|Runtime\\.exec|subprocess|subprocess\\.run|os\\.system|commands\\.getoutput|subprocess\\.call|subprocess\\.Popen|\\$\\(|backtick|`\")".to_string());
                        attrs
                    },
                    children_pattern: None,
                },
            ],
        },
        language_specific: false,
        languages: vec![
            "python".into(), "javascript".into(), "typescript".into(),
            "java".into(), "csharp".into(), "ruby".into(), "go".into(),
            "php".into(), "rust".into(), "perl".into(),
        ],
        severity_default: SeverityLevel::Critical,
        confidence: 0.93,
        remediation: "Avoid passing user input to shell commands. Use parameterized APIs, \
            whitelist allowed commands, or sandboxed execution.".to_string(),
        fix: Some("subprocess.run(['ls', '-la', user_input], shell=False)".to_string()),
        owasp_category: Some("A03:2021-Injection".to_string()),
        examples_vulnerable: vec![
            "os.system('ping ' + user_input)".to_string(),
            "exec('ls ' + req.query.dir)".to_string(),
            "Runtime.getRuntime().exec('cat ' + filename)".to_string(),
            "`grep \"{$user_input}\" file.txt`".to_string(),  // Ruby backticks
            "subprocess.call('rm -rf ' + path, shell=True)".to_string(),
            "goexec('whoami ' + userInput)".to_string(),
        ],
        examples_safe: vec![
            "subprocess.run(['ls', '-la'], shell=False)".to_string(),
            "ProcessBuilder.new().command('ls', user_input).start()".to_string(),
            "exec('ls', [user_input]) // No shell interpolation".to_string(),
        ],
    });

    // =====================
    // CODE INJECTION (CWE-94)
    // =====================
    db.register(PatternRule {
        id: "INJ-CODE-001".to_string(),
        cwe_id: "CWE-94".to_string(),
        name: "Code Injection via eval/exec".to_string(),
        description: "User-supplied input is passed to code execution functions \
            like eval(), exec(), Function(), setTimeout(string), etc.".to_string(),
        pattern: PatternDefinition::AstPattern {
            node_type: "ExprCall".to_string(),
            attributes: {
                let mut attrs = HashMap::new();
                attrs.insert("function_name".to_string(),
                    "(eval|exec|Function|vm\\.runInThisContext|setTimeout|setInterval|\\$\\(eval\\)|load|dofile|loadfile)".to_string());
                attrs
            },
            children_pattern: None,
        },
        language_specific: false,
        languages: vec![
            "python".into(), "javascript".into(), "typescript".into(),
            "ruby".into(), "lua".into(), "php".into(), "go".into(),
        ],
        severity_default: SeverityLevel::Critical,
        confidence: 0.97,
        remediation: "Never pass user input to code execution functions. Use safe alternatives \
            like JSON.parse() instead of eval().".to_string(),
        fix: Some("JSON.parse(userInput)  // Instead of eval(userInput)".to_string()),
        owasp_category: Some("A03:2021-Injection".to_string()),
        examples_vulnerable: vec![
            "eval(userInput)".to_string(),
            "exec(request.POST['code'])".to_string(),
            "new Function('return ' + userInput)()".to_string(),
            "vm.runInThisContext(userInput)".to_string(),
            "setTimeout(userInput, 1000)".to_string(),
            "dofile(userInput)".to_string(),
            "load(userInput)".to_string(),
            "instance_eval(params[:code])".to_string(),
        ],
        examples_safe: vec![
            "JSON.parse(userInput)".to_string(),
            "parseInt(userInput, 10)".to_string(),
            "parseFloat(userInput)".to_string(),
        ],
    });

    // =====================
    // LDAP INJECTION (CWE-90)
    // =====================
    db.register(PatternRule {
        id: "INJ-LDAP-001".to_string(),
        cwe_id: "CWE-90".to_string(),
        name: "LDAP Injection".to_string(),
        description: "User input is used in LDAP queries without proper escaping, \
            allowing attackers to manipulate directory searches.".to_string(),
        pattern: PatternDefinition::Composite {
            operator: crate::patterns::CompositeOp::And,
            patterns: vec![
                PatternDefinition::AstPattern {
                    node_type: "ExprCall".to_string(),
                    attributes: {
                        let mut attrs = HashMap::new();
                        attrs.insert("function_name".to_string(),
                            "(ldap_search|ldap_bind|search_s|search\\(|\\.search\\(|LDAPConnection\\.search)".to_string());
                        attrs
                    },
                    children_pattern: Some(Box::new(PatternDefinition::DataFlow {
                        sources: vec!["request".into(), "input".into(), "user".into(), "params".into()],
                        sinks: vec!["ldap_search".into(), "ldap_bind".into(), "search".into()],
                        sanitizers: vec!["ldap_escape".into(), "filter_var".into()],
                    })),
                },
            ],
        },
        language_specific: false,
        languages: vec![
            "python".into(), "java".into(), "php".into(), "csharp".into(),
        ],
        severity_default: SeverityLevel::High,
        confidence: 0.85,
        remediation: "Escape all user input before using in LDAP queries. \
            Use positive allowlists for search filters.".to_string(),
        fix: Some(
            "from ldap.filterfilter import escape_filter_chars\n\
             safe_query = escape_filter_chars(userInput)\n\
             ldap.search_s('dc=example,dc=com', ldap.SCOPE_SUBTREE, safe_query)"
                .to_string(),
        ),
        owasp_category: Some("A03:2021-Injection".to_string()),
        examples_vulnerable: vec![
            "ldap.search_s('dc=example,dc=com', ldap.SCOPE_SUBTREE, '(uid=' + username + ')')".to_string(),
            "$query = \"(uid=\" . $_GET['username'] . \")\"; ldap_search($conn, $dn, $query)".to_string(),
        ],
        examples_safe: vec![
            "ldap.search_s('dc=example,dc=com', ldap.SCOPE_SUBTREE, ldap.filter_format('(uid=%s)', [username]))".to_string(),
        ],
    });

    // =====================
    // XPATH INJECTION (CWE-643)
    // =====================
    db.register(PatternRule {
        id: "INJ-XPATH-001".to_string(),
        cwe_id: "CWE-643".to_string(),
        name: "XPath Injection".to_string(),
        description: "User input is used in XPath expressions without proper \
            quoting or parameterization.".to_string(),
        pattern: PatternDefinition::Composite {
            operator: crate::patterns::CompositeOp::And,
            patterns: vec![
                PatternDefinition::AstPattern {
                    node_type: "ExprCall".to_string(),
                    attributes: {
                        let mut attrs = HashMap::new();
                        attrs.insert("function_name".to_string(),
                            "(xpath|evaluate|compile_xpath|\\.evaluate|\\.select|find\\(|XPathExpression)".to_string());
                        attrs
                    },
                    children_pattern: None,
                },
            ],
        },
        language_specific: false,
        languages: vec![
            "python".into(), "java".into(), "javascript".into(), "php".into(), "csharp".into(),
        ],
        severity_default: SeverityLevel::High,
        confidence: 0.82,
        remediation: "Use parameterized XPath queries or escape user input properly.".to_string(),
        fix: Some(
            "XPathExpression expr = xpath.compile(\"/users/user[@id=$id]\");\n\
             expr.setParameter(QName.valueOf(\"id\"), userId);"
                .to_string(),
        ),
        owasp_category: Some("A03:2021-Injection".to_string()),
        examples_vulnerable: vec![
            "doc.xpath('//user[username=\"' + username + '\"]')".to_string(),
            "// Java\nxpath.evaluate(\"/users/user[name='\" + name + \"']\", doc);".to_string(),
        ],
        examples_safe: vec![
            "// Use parameterized XPath\nlet expr = xpath.compile(\"/users/user[@id=$id]\");\nexpr.bind_variable('id', userId);".to_string(),
        ],
    });

    // =====================
    // NO-SQL INJECTION (CWE-943)
    // =====================
    db.register(PatternRule {
        id: "INJ-NOSQL-001".to_string(),
        cwe_id: "CWE-943".to_string(),
        name: "NoSQL Injection".to_string(),
        description: "User input is used in NoSQL database queries without \
            proper sanitization, allowing query manipulation.".to_string(),
        pattern: PatternDefinition::Composite {
            operator: crate::patterns::CompositeOp::Or,
            patterns: vec![
                // MongoDB-style injection
                PatternDefinition::AstPattern {
                    node_type: "ExprCall".to_string(),
                    attributes: {
                        let mut attrs = HashMap::new();
                        attrs.insert("function_name".to_string(),
                            "(\\.find\\(|\\.findOne\\(|\\.insert\\(|\\.update\\(|\\.aggregate\\(|db\\.\\w+\\.find|collection\\.\\w+)".to_string());
                        attrs
                    },
                    children_pattern: Some(Box::new(PatternDefinition::DataFlow {
                        sources: vec!["req".into(), "request".into(), "body".into(), "input".into(), "params".into()],
                        sinks: vec!["find".into(), "findOne".into(), "insert".into()],
                        sanitizers: vec!["sanitize".into(), "validate".into(), "escape".into()],
                    })),
                },
                // Firebase-style injection
                PatternDefinition::AstPattern {
                    node_type: "ExprCall".to_string(),
                    attributes: {
                        let mut attrs = HashMap::new();
                        attrs.insert("function_name".to_string(),
                            "(orderByChild|orderByKey|orderByValue|equalTo|startAt|endAt)".to_string());
                        attrs
                    },
                    children_pattern: None,
                },
            ],
        },
        language_specific: false,
        languages: vec![
            "python".into(), "javascript".into(), "typescript".into(),
            "java".into(), "csharp".into(), "go".into(),
        ],
        severity_default: SeverityLevel::High,
        confidence: 0.88,
        remediation: "Use parameterized queries and input validation for NoSQL databases.".to_string(),
        fix: Some("collection.find({ name: req.body.name })  // Don't build query from raw input".to_string()),
        owasp_category: Some("A03:2021-Injection".to_string()),
        examples_vulnerable: vec![
            "db.collection.find(JSON.parse(userInput))".to_string(),
            "Users.find({ username: req.body.username })".to_string(), // If username contains { \"$ne\": \"\" }
            "ref.orderByChild('age').equalTo(req.query.age)".to_string(),
        ],
        examples_safe: vec![
            "collection.find_one({'name': validated_name})".to_string(),
            "collection.find({'id': {'$oid': sanitized_id}})".to_string(),
        ],
    });

    // =====================
    // HEADER INJECTION (CWE-113)
    // =====================
    db.register(PatternRule {
        id: "INJ-HDR-001".to_string(),
        cwe_id: "CWE-113".to_string(),
        name: "HTTP Response Splitting / Header Injection".to_string(),
        description: "User input is written directly to HTTP headers, allowing \
            an attacker to inject CRLF characters and forge new headers or responses.".to_string(),
        pattern: PatternDefinition::AstPattern {
            node_type: "ExprCall".to_string(),
            attributes: {
                let mut attrs = HashMap::new();
                attrs.insert("function_name".to_string(),
                    "(setHeader|res\\.set|res\\.header|response\\.addHeader|header\\()".to_string());
                attrs
            },
            children_pattern: Some(Box::new(PatternDefinition::DataFlow {
                sources: vec!["req".into(), "request".into(), "input".into()],
                sinks: vec!["setHeader".into(), "set".into(), "header".into()],
                sanitizers: vec!["replace".into(), "strip_tags".into()],
            })),
        },
        language_specific: false,
        languages: vec![
            "javascript".into(), "typescript".into(), "java".into(), "php".into(), "python".into(),
        ],
        severity_default: SeverityLevel::Medium,
        confidence: 0.85,
        remediation: "Validate and sanitize user input before using it in HTTP headers. \
            Reject input containing CR (\\r) or LF (\\n) characters.".to_string(),
        fix: Some("res.setHeader('Location', sanitizeHeader(userInput))".to_string()),
        owasp_category: Some("A03:2021-Injection".to_string()),
        examples_vulnerable: vec![
            "res.setHeader('X-Custom', req.query.custom)".to_string(),
            "header('Location: ' . $_GET['url'])".to_string(),
        ],
        examples_safe: vec![
            "res.setHeader('X-Custom', encodeURIComponent(req.query.custom))".to_string(),
        ],
    });
}
