// Detector automático de formato de instalável via magic bytes + extensão
import * as path from 'path';

export interface InstallerFormat {
  extension: string;
  magicBytes: Uint8Array[];  // Assinaturas binárias conhecidas
  parser: string;            // Nome do parser a usar
  platform: 'windows' | 'linux' | 'android' | 'ios' | 'macos' | 'cross';
  metadata: {
    manifestPath: string | null;   // Caminho relativo ao manifest dentro do pacote
    signaturePath: string | null;  // Caminho à assinatura digital
    supportedOps: string[];  // Operações suportadas (install, update, verify)
  };
}

export const INSTALLER_FORMATS: Record<string, InstallerFormat> = {
  // Windows
  'msi': {
    extension: '.msi',
    magicBytes: [
      new Uint8Array([0xD0, 0xCF, 0x11, 0xE0, 0xA1, 0xB1, 0x1A, 0xE1]), // OLE Compound File
    ],
    parser: 'MsiExtendedFrontend',
    platform: 'windows',
    metadata: {
      manifestPath: null, // MSI não tem manifest separado
      signaturePath: '_DigitalSignature',
      supportedOps: ['install', 'repair', 'uninstall', 'advertise']
    }
  },
  'exe-nsis': {
    extension: '.exe',
    magicBytes: [
      new Uint8Array([0xEF, 0xBE, 0xAD, 0xDE]), // NSIS signature
      new Uint8Array([0x4D, 0x5A]), // PE header fallback
    ],
    parser: 'ExeWrapperParser',
    platform: 'windows',
    metadata: {
      manifestPath: null,
      signaturePath: null, // Assinatura via Authenticode
      supportedOps: ['install', 'silent']
    }
  },
  'appx': {
    extension: '.appx',
    magicBytes: [new Uint8Array([0x50, 0x4B, 0x03, 0x04])], // ZIP header
    parser: 'AppxManifestParser',
    platform: 'windows',
    metadata: {
      manifestPath: 'AppxManifest.xml',
      signaturePath: '[Content_Types].xml',
      supportedOps: ['install', 'update', 'verify']
    }
  },

  // Linux
  'deb': {
    extension: '.deb',
    magicBytes: [new Uint8Array([0x21, 0x3C, 0x61, 0x72, 0x63, 0x68, 0x3E, 0x0A])], // "!<arch>\n"
    parser: 'DebControlParser',
    platform: 'linux',
    metadata: {
      manifestPath: 'control.tar.gz/control',
      signaturePath: null, // Assinatura via dpkg-sig
      supportedOps: ['install', 'upgrade', 'remove']
    }
  },
  'rpm': {
    extension: '.rpm',
    magicBytes: [new Uint8Array([0xED, 0xAB, 0xEE, 0xDB])], // RPM magic
    parser: 'RpmSpecParser',
    platform: 'linux',
    metadata: {
      manifestPath: null, // Spec embutido no header
      signaturePath: null, // Assinatura via GPG no header
      supportedOps: ['install', 'upgrade', 'verify', 'query']
    }
  },

  // Android
  'apk': {
    extension: '.apk',
    magicBytes: [new Uint8Array([0x50, 0x4B, 0x03, 0x04])], // ZIP
    parser: 'ApkManifestParser',
    platform: 'android',
    metadata: {
      manifestPath: 'AndroidManifest.xml',
      signaturePath: 'META-INF/',
      supportedOps: ['install', 'verify', 'extract']
    }
  },
  'aab': {
    extension: '.aab',
    magicBytes: [new Uint8Array([0x50, 0x4B, 0x03, 0x04])], // ZIP
    parser: 'AabBundleParser',
    platform: 'android',
    metadata: {
      manifestPath: 'base/manifest/AndroidManifest.xml',
      signaturePath: 'META-INF/',
      supportedOps: ['bundle', 'verify', 'extract']
    }
  },

  // iOS
  'ipa': {
    extension: '.ipa',
    magicBytes: [new Uint8Array([0x50, 0x4B, 0x03, 0x04])], // ZIP
    parser: 'IpaInfoPlistParser',
    platform: 'ios',
    metadata: {
      manifestPath: 'Payload/*.app/Info.plist',
      signaturePath: 'Payload/*.app/_CodeSignature/',
      supportedOps: ['install', 'verify', 'extract']
    }
  },

  // macOS
  'pkg': {
    extension: '.pkg',
    magicBytes: [new Uint8Array([0x50, 0x4B, 0x03, 0x04])], // XAR/ZIP
    parser: 'PkgDistributionParser',
    platform: 'macos',
    metadata: {
      manifestPath: 'Distribution',
      signaturePath: null, // Assinatura via codesign
      supportedOps: ['install', 'verify', 'extract']
    }
  },
  'dmg': {
    extension: '.dmg',
    magicBytes: [
      new Uint8Array([0x78, 0x01, 0x73, 0x0D, 0x62, 0x62, 0x60]), // UDIF
      new Uint8Array([0x6B, 0x6F, 0x6C, 0x79]), // koly trailer
    ],
    parser: 'DmgVolumeParser',
    platform: 'macos',
    metadata: {
      manifestPath: null,
      signaturePath: null,
      supportedOps: ['mount', 'verify', 'extract']
    }
  }
};

export class InstallerFormatDetector {
  static async detectFormat(filePath: string, buffer: Uint8Array): Promise<InstallerFormat | null> {
    const ext = path.extname(filePath).slice(1).toLowerCase();

    // Tentar por extensão primeiro
    if (INSTALLER_FORMATS[ext]) {
      const format = INSTALLER_FORMATS[ext];
      // Validar magic bytes se fornecido buffer
      if (buffer && format.magicBytes.length > 0) {
        for (const magic of format.magicBytes) {
          if (this._matchesMagic(buffer, magic)) {
            return format;
          }
        }
        // Extensão não bate com magic bytes → possível falsificação
        throw new Error(`Format mismatch: extension .${ext} does not match detected magic bytes`);
      }
      return format;
    }

    // Fallback: detectar por magic bytes
    for (const [key, format] of Object.entries(INSTALLER_FORMATS)) {
      for (const magic of format.magicBytes) {
        if (this._matchesMagic(buffer, magic)) {
          return format;
        }
      }
    }

    return null; // Formato não reconhecido
  }

  private static _matchesMagic(buffer: Uint8Array, magic: Uint8Array): boolean {
    if (buffer.length < magic.length) return false;
    for (let i = 0; i < magic.length; i++) {
      if (buffer[i] !== magic[i]) return false;
    }
    return true;
  }
}
