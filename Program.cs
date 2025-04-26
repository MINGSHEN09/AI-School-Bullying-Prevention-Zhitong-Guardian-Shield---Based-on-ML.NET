using Microsoft.ML;
using Ml;
using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading;

// 配置参数
string picturesFolder = Environment.GetFolderPath(Environment.SpecialFolder.MyPictures);
string sourceFolder = Path.Combine(picturesFolder, "未处理");
string outputRoot = Path.Combine(picturesFolder, "已处理", "分类", "霸凌");
string logPath = Path.Combine(outputRoot, $"classification_log_{DateTime.Now:yyyyMMdd_HHmmss}.csv");
float confidenceThreshold = 0.98f;
string lowConfidenceCategory = "低置信度结果";
string[] allowedExtensions = { ".jpg", ".jpeg", ".png", ".bmp" };

// 初始化必要目录
Directory.CreateDirectory(sourceFolder);
Directory.CreateDirectory(outputRoot);

// 初始化日志文件
File.WriteAllText(logPath, "原始路径,分类目录,预测类别,原始置信度,置信状态,移动状态,时间戳\n", Encoding.UTF8);

Console.WriteLine($"监控目录：{sourceFolder}");
Console.WriteLine($"分类阈值设置：{confidenceThreshold:P0}");
Console.WriteLine($"低置信度分类名称：{lowConfidenceCategory}\n");

try
{
    while (true)
    {
        var imageFiles = Directory.GetFiles(sourceFolder, "*.*", SearchOption.AllDirectories)
            .Where(file => allowedExtensions.Any(ext => file.EndsWith(ext, StringComparison.OrdinalIgnoreCase)))
            .ToList();

        if (imageFiles.Count > 0)
        {
            foreach (var imagePath in imageFiles)
            {
                string relativePath = "";
                string destPath = "";
                string status = "";
                string category = "";
                string confidenceStatus = "";
                float originalConfidence = 0;

                try
                {
                    relativePath = Path.GetRelativePath(sourceFolder, imagePath);
                    var imageBytes = File.ReadAllBytes(imagePath);
                    var predictions = MLModel1.PredictAllLabels(new MLModel1.ModelInput { ImageSource = imageBytes });
                    var topResult = predictions.First();

                    originalConfidence = topResult.Value;
                    category = originalConfidence >= confidenceThreshold ?
                              topResult.Key :
                              $"{lowConfidenceCategory}({topResult.Key})";
                    confidenceStatus = originalConfidence >= confidenceThreshold ?
                                      "达标" :
                                      $"不足({originalConfidence:P0}<{confidenceThreshold:P0})";

                    destPath = Path.Combine(outputRoot, category, relativePath);
                    Directory.CreateDirectory(Path.GetDirectoryName(destPath));

                    File.Move(imagePath, destPath);
                    status = "成功";
                }
                catch (Exception ex)
                {
                    status = $"失败：{ex.Message.Replace(',', ';')}";
                    destPath = "未移动";
                }
                finally
                {
                    // 记录日志
                    var logEntry = $"\"{imagePath}\",\"{destPath}\",\"{category}\"," +
                                 $"{originalConfidence:F4},\"{confidenceStatus}\"," +
                                 $"\"{status}\",{DateTime.Now:yyyy-MM-dd HH:mm:ss}";
                    File.AppendAllText(logPath, logEntry + Environment.NewLine, Encoding.UTF8);

                    // 控制台输出
                    Console.ForegroundColor = originalConfidence >= confidenceThreshold ? ConsoleColor.Green : ConsoleColor.Yellow;
                    Console.WriteLine($"[{status}] {Path.GetFileName(imagePath)} " +
                                    $"-> {category} ({originalConfidence:P0}) " +
                                    $"{(confidenceStatus.Contains("不足") ? "⚠" : "")}");
                    Console.ResetColor();
                }
            }
        }
        else
        {
            Console.WriteLine("等待新文件中..." + DateTime.Now.ToString("HH:mm:ss"));
        }

        // 每秒检测一次
        Thread.Sleep(1000);
    }
}
catch (Exception ex)
{
    Console.WriteLine($"程序终止：{ex.Message}");
}