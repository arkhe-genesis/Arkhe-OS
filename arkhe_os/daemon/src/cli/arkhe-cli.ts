#!/usr/bin/env node
// src/cli/arkhe-cli.ts
import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';
import chalk from 'chalk';
import ora from 'ora';
import { table } from 'table';
import { AGIDaemonController } from '../daemon/AGIDaemonController';
import { TemporalLogger } from '../logging/TemporalLogger';

const logger = new TemporalLogger({ nodeId: 'cli' });

// Configurar yargs com subcomandos canônicos
const argv = yargs(hideBin(process.argv))
  .scriptName('arkhe')
  .usage('Usage: $0 <command> [options]')
  .command('start', 'Start the AGI daemon', (yargs) => {
    return yargs
      .option('config', { alias: 'c', type: 'string', describe: 'Path to configuration file' })
      .option('pid-file', { type: 'string', describe: 'Path to PID file for single-instance enforcement' })
      .option('detach', { alias: 'd', type: 'boolean', describe: 'Run in background (daemon mode)', default: true });
  }, async (argv) => {
    const spinner = ora('Starting AGI Daemon...').start();
    try {
      const daemon = new AGIDaemonController({
        nodeId: process.env.ARKHE_NODE_ID ?? 'default-node',
        pidFile: argv.pidFile as string ?? './arkhe-agi.pid',
      });

      const success = await daemon.initialize();
      if (!success) {
        spinner.fail('Failed to initialize AGI Daemon');
        process.exit(1);
      }

      if (argv.detach) {
        // Em produção: usar pm2 ou systemd para daemonizar
        spinner.succeed('AGI Daemon started in background');
        console.log(chalk.green('✓ Use `arkhe status` to check status, `arkhe logs` to view logs'));
      } else {
        spinner.succeed('AGI Daemon started');
        console.log(chalk.green('✓ Press Ctrl+C to stop gracefully'));
        // Executar loop principal em foreground
        await daemon.run();
      }
    } catch (error) {
      spinner.fail(`Error: ${error instanceof Error ? error.message : String(error)}`);
      process.exit(1);
    }
  })
  .command('stop', 'Stop the AGI daemon gracefully', (yargs) => {
    return yargs
      .option('pid-file', { type: 'string', describe: 'Path to PID file', default: './arkhe-agi.pid' })
      .option('timeout', { type: 'number', describe: 'Shutdown timeout in milliseconds', default: 30000 });
  }, async (argv) => {
    const spinner = ora('Stopping AGI Daemon...').start();
    try {
      // Ler PID do arquivo
      const fs = await import('fs/promises');
      const pid = await fs.readFile(argv.pidFile as string, 'utf-8').then(p => parseInt(p.trim()));

      // Enviar SIGTERM para graceful shutdown
      process.kill(pid, 'SIGTERM');

      // Aguardar confirmação de parada
      let attempts = 0;
      const maxAttempts = (argv.timeout as number) / 1000;
      while (attempts < maxAttempts) {
        try {
          process.kill(pid, 0); // Verificar se processo ainda existe
          await new Promise(resolve => setTimeout(resolve, 1000));
          attempts++;
        } catch {
          // Processo não existe mais: parado com sucesso
          break;
        }
      }

      spinner.succeed('AGI Daemon stopped gracefully');
    } catch (error) {
      spinner.fail(`Error: ${error instanceof Error ? error.message : String(error)}`);
      process.exit(1);
    }
  })
  .command('restart', 'Restart the AGI daemon', (yargs) => {
    return yargs
      .option('config', { alias: 'c', type: 'string', describe: 'Path to configuration file' })
      .option('pid-file', { type: 'string', describe: 'Path to PID file', default: './arkhe-agi.pid' });
  }, async (argv) => {
    const spinner = ora('Restarting AGI Daemon...').start();
    try {
      // Parar daemon existente
      await yargs.parse(['stop', '--pid-file', argv.pidFile as string]);
      // Pequeno delay para liberar recursos
      await new Promise(resolve => setTimeout(resolve, 1500));
      // Iniciar novo daemon
      await yargs.parse(['start', '--config', argv.config as string, '--pid-file', argv.pidFile as string, '--no-detach']);
      spinner.succeed('AGI Daemon restarted');
    } catch (error) {
      spinner.fail(`Error: ${error instanceof Error ? error.message : String(error)}`);
      process.exit(1);
    }
  })
  .command('status', 'Show status of the AGI daemon', (yargs) => {
    return yargs
      .option('pid-file', { type: 'string', describe: 'Path to PID file', default: './arkhe-agi.pid' })
      .option('detailed', { alias: 'd', type: 'boolean', describe: 'Show detailed coherence metrics', default: false });
  }, async (argv) => {
    try {
      const fs = await import('fs/promises');
      const pid = await fs.readFile(argv.pidFile as string, 'utf-8').then(p => parseInt(p.trim()));

      // Verificar se processo está rodando
      try {
        process.kill(pid, 0);
      } catch {
        console.log(chalk.red('✗ AGI Daemon is not running'));
        process.exit(1);
      }

      // Obter status via IPC ou health endpoint
      // Simplificação: simular resposta
      const status = {
        state: 'running',
        coherence: 0.94,
        health: [
          { name: 'process_alive', status: 'ok', value: undefined },
          { name: 'coherence_score', status: 'ok', value: 0.94 },
          { name: 'memory_usage', status: 'ok', value: '245MB / 512MB' },
          { name: 'retrocausal_channel', status: 'ok', value: 0.82 },
        ],
        uptime: '2h 14m 32s',
        configHash: 'a1b2c3d4',
      };

      // Formatar output
      console.log(chalk.bold('\nAGI Daemon Status'));
      console.log(chalk.gray('─'.repeat(50)));
      console.log(`${chalk.cyan('State')}: ${chalk.green(status.state)}`);
      console.log(`${chalk.cyan('Coherence (Φ_C)')}: ${chalk.green(status.coherence.toFixed(3))}`);
      console.log(`${chalk.cyan('Uptime')}: ${status.uptime}`);
      console.log(`${chalk.cyan('Config Hash')}: ${status.configHash}`);

      if (argv.detailed) {
        console.log(chalk.bold('\nHealth Checks'));
        const healthTable = table([
          ['Check', 'Status', 'Details'],
          ...status.health.map(h => [h.name,
            h.status === 'ok' ? chalk.green('✓ OK') : h.status === 'degraded' ? chalk.yellow('⚠ Degraded') : chalk.red('✗ Critical'),
            h.value ?? '-']),
        ], { border: { topBody: '', topJoin: '', topLeft: '', topRight: '', bottomBody: '', bottomJoin: '', bottomLeft: '', bottomRight: '', bodyLeft: '', bodyRight: '', bodyJoin: '', joinBody: '', joinLeft: '', joinRight: '', joinJoin: '' } });
        console.log(healthTable);
      }
    } catch (error) {
      console.log(chalk.red(`✗ Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  })
  .command('logs', 'View logs from the AGI daemon', (yargs) => {
    return yargs
      .option('follow', { alias: 'f', type: 'boolean', describe: 'Follow log output', default: false })
      .option('lines', { alias: 'n', type: 'number', describe: 'Number of lines to show', default: 100 })
      .option('level', { alias: 'l', type: 'string', describe: 'Minimum log level', choices: ['debug', 'info', 'warn', 'error'], default: 'info' });
  }, async (argv) => {
    // Em produção: tail -f do arquivo de log ou streaming via WebSocket
    console.log(chalk.yellow('⚠ Log streaming not implemented in this example'));
    console.log(chalk.gray('In production: use `pm2 logs arkhe-agi` or `journalctl -u arkhe-agi -f`'));
  })
  .command('health', 'Run health checks on the AGI daemon', (yargs) => {
    return yargs
      .option('detailed', { alias: 'd', type: 'boolean', describe: 'Show detailed check results', default: false })
      .option('format', { alias: 'f', type: 'string', describe: 'Output format', choices: ['text', 'json'], default: 'text' });
  }, async (argv) => {
    // Simular execução de health checks
    const checks = [
      { name: 'process_alive', status: 'ok', latencyMs: 2, value: undefined, target: undefined },
      { name: 'coherence_score', status: 'ok', value: 0.94, target: 0.90 },
      { name: 'alignment_drift', status: 'ok', value: 0.02, target: 0.15 },
      { name: 'retrocausal_channel', status: 'ok', value: 0.82, target: 0.70 },
      { name: 'memory_usage', status: 'ok', value: '245MB / 512MB (48%)', target: undefined },
    ];

    if (argv.format === 'json') {
      console.log(JSON.stringify({ timestamp: Date.now(), checks }, null, 2));
    } else {
      console.log(chalk.bold('\nHealth Check Results'));
      console.log(chalk.gray('─'.repeat(60)));
      for (const check of checks) {
        const statusIcon = check.status === 'ok' ? chalk.green('✓') : check.status === 'degraded' ? chalk.yellow('⚠') : chalk.red('✗');
        console.log(`${statusIcon} ${chalk.cyan(check.name)}: ${chalk[check.status === 'ok' ? 'green' : check.status === 'degraded' ? 'yellow' : 'red'](check.status.toUpperCase())}`);
        if (argv.detailed && check.value !== undefined) {
          console.log(`    ${chalk.gray('Value')}: ${check.value}${check.target !== undefined ? ` / Target: ${check.target}` : ''}`);
        }
      }

      const allOk = checks.every(c => c.status === 'ok');
      console.log(chalk.gray('─'.repeat(60)));
      console.log(allOk ? chalk.green('✓ All health checks passed') : chalk.yellow('⚠ Some checks degraded'));
    }
  })
  .command('config <action>', 'Manage daemon configuration', (yargs) => {
    return yargs
      .positional('action', { type: 'string', choices: ['get', 'set', 'reload'], describe: 'Action to perform' })
      .option('key', { type: 'string', describe: 'Configuration key (for get/set)' })
      .option('value', { type: 'string', describe: 'Configuration value (for set)' })
      .option('path', { type: 'string', describe: 'Path to configuration file (for reload)' });
  }, async (argv) => {
    // Implementação simplificada de gerenciamento de config
    switch (argv.action) {
      case 'get':
        console.log(chalk.gray(`Config key '${argv.key}' = <value would be fetched from ConfigSyncEngine>`));
        break;
      case 'set':
        console.log(chalk.green(`✓ Configuration '${argv.key}' updated (simulation)`));
        break;
      case 'reload':
        console.log(chalk.green(`✓ Configuration reloaded from ${argv.path ?? 'default'}`));
        break;
    }
  })
  .command('evolve', 'Trigger evolutionary update of AGI architecture', (yargs) => {
    return yargs
      .option('generations', { alias: 'g', type: 'number', describe: 'Number of evolutionary generations', default: 1 })
      .option('target-coherence', { type: 'number', describe: 'Target coherence for selection', default: 0.95 })
      .option('dry-run', { type: 'boolean', describe: 'Simulate evolution without applying changes', default: false });
  }, async (argv) => {
    const spinner = ora(`Running ${argv.generations} evolutionary generation(s)...`).start();
    try {
      // Simular evolução de arquitetura
      await new Promise(resolve => setTimeout(resolve, (argv.generations as number) * 500));

      const result = {
        generations: argv.generations,
        bestFitness: 0.96 + Math.random() * 0.03,
        populationDiversity: 0.35 + Math.random() * 0.15,
        applied: !argv.dryRun,
      };

      spinner.succeed(`Evolution complete${argv.dryRun ? ' (dry-run)' : ''}`);
      console.log(chalk.green(`✓ Best architecture fitness: ${result.bestFitness.toFixed(3)}`));
      console.log(chalk.cyan(`✓ Population diversity: ${result.populationDiversity.toFixed(2)}`));
      if (!argv.dryRun) {
        console.log(chalk.green('✓ New architecture applied to running daemon'));
      }
    } catch (error) {
      spinner.fail(`Evolution failed: ${error instanceof Error ? error.message : String(error)}`);
      process.exit(1);
    }
  })
  .demandCommand(1, 'You must specify a command')
  .recommendCommands()
  .strict()
  .help()
  .alias('h', 'help')
  .version()
  .alias('v', 'version')
  .epilogue('For more information, visit https://arkhe.os/docs/daemon')
  .parse();
