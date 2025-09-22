import { fileURLToPath } from 'url';
import fs from 'fs';
import path from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * 清空目录下所有文件的内容
 * @param {string} dirPath - 目录路径
 */
function clearDirectoryContents(dirPath) {
    try {
        if (!fs.existsSync(dirPath)) {
            console.log(`目录不存在: ${dirPath}`);
            return;
        }

        const files = fs.readdirSync(dirPath);
        files.forEach(file => {
            const filePath = path.join(dirPath, file);
            const stat = fs.statSync(filePath);

            if (stat.isFile()) {
                // 清空文件内容
                fs.writeFileSync(filePath, '', 'utf8');
                console.log(`已清空文件: ${filePath}`);
            } else if (stat.isDirectory()) {
                // 递归清空子目录
                clearDirectoryContents(filePath);
            }
        });

        console.log(`已清空目录内容: ${dirPath}`);
    } catch (error) {
        console.error(`清空目录失败 ${dirPath}:`, error.message);
    }
}

/**
 * 清空指定文件内容
 * @param {string} filePath - 文件路径
 */
function clearFileContent(filePath) {
    try {
        if (!fs.existsSync(filePath)) {
            console.log(`文件不存在: ${filePath}`);
            return;
        }

        fs.writeFileSync(filePath, '', 'utf8');
        console.log(`已清空文件内容: ${filePath}`);
    } catch (error) {
        console.error(`清空文件失败 ${filePath}:`, error.message);
    }
}

/**
 * 执行清理工作
 */
function cleanup() {
    console.log('开始执行清理...');

    // 获取项目根目录
    const projectRoot = path.resolve(__dirname, '..');

    // 清空 cache 目录下所有文件的内容
    const cacheDir = path.join(projectRoot, 'cache');
    clearDirectoryContents(cacheDir);

    // 清空 config 目录下 log.txt 的内容
    const configLogFile = path.join(projectRoot, 'config', 'log.txt');
    clearFileContent(configLogFile);

    console.log('清理完成！');
}

// 执行清理
cleanup();
