const fs = require('fs');
let content = fs.readFileSync('server/types.ts', 'utf8');
content = content.replace(
  /export interface LatentCoherenceResults {[\s\S]*?avg_lambda_coct: number;/g,
  `export interface LatentCoherenceResults {
  summary: {
    avg_lambda_cot: number;
    avg_lambda_coct: number;
  };
}`
);
fs.writeFileSync('server/types.ts', content);

content = fs.readFileSync('src/components/ClusterOrchestrationPanel.tsx', 'utf8');
content = content.replace(
  /\{\(\(cluster\?\.logs\?\.length \?\? 0\) > 0\) && \(\s*\{cluster\.logs\.length > 0 && \(/g,
  `{((cluster?.logs?.length ?? 0) > 0) && (`
);
content = content.replace(
  /isDeploying \|\| cluster\?\.status === 'resonant'\s*\?\s*'bg-\[#111214\] text-arkhe-muted border border-arkhe-border cursor-not-allowed'\s*isDeploying \|\| cluster\.status === 'resonant'/g,
  `isDeploying || cluster?.status === 'resonant'`
);

content = content.replace(
  /\{\(\(deployLogs \?\? \[\]\)\.map\)\(\(log, i\) => \(\s*<motion\.div/g,
  `{(deployLogs ?? []).map((log, i) => (
                    <motion.div`
);

content = content.replace(
  /<motion\.div\s*$/m,
  `<motion.div
                        key={i}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="text-arkhe-muted"
                      >
                        <span className="text-emerald-500/50 mr-2">[{new Date().toLocaleTimeString()}]</span>
                        {log}
                      </motion.div>
                  ))}
                </div>
              </div>`
);


fs.writeFileSync('src/components/ClusterOrchestrationPanel.tsx', content);
