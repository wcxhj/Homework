import os
from pathlib import Path
import sys
# 添加当前目录到系统路径，以便导入pdf_mineru_local
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from pdf_mineru_local import upload_local_file_to_remote

def test_upload():
    """
    测试上传功能
    """
    # 使用项目中的示例PDF文件进行测试
    dummy_pdf_path = Path("./dummy_report.pdf").resolve()
    
    if not dummy_pdf_path.exists():
        print(f"示例PDF文件不存在: {dummy_pdf_path}")
        # 尝试在项目根目录查找
        root_dir_pdf = Path("../../dummy_report.pdf").resolve()
        if root_dir_pdf.exists():
            dummy_pdf_path = root_dir_pdf
        else:
            print("未找到示例PDF文件，创建一个测试文件...")
            # 创建一个简单的PDF测试文件
            dummy_pdf_path = Path("./test_dummy_report.pdf").resolve()
            create_test_pdf(dummy_pdf_path)
    
    print(f"开始上传测试文件: {dummy_pdf_path}")
    
    try:
        result_url = upload_local_file_to_remote(dummy_pdf_path)
        print(f"上传结果URL: {result_url}")
        
        if result_url and result_url.startswith("mineru_direct://"):
            print("使用了minerU直接上传功能")
        elif result_url and ("file.io" in result_url or "transfer.sh" in result_url or 
                             "uguu.se" in result_url or "oss" in result_url):
            print("文件上传成功!")
        elif result_url:
            print("使用了回退URL方案 - 文件可能未实际上传")
        else:
            print("上传失败")
            
        return result_url
    except Exception as e:
        print(f"上传失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_test_pdf(pdf_path):
    """
    创建一个简单的PDF测试文件
    """
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        c = canvas.Canvas(str(pdf_path), pagesize=letter)
        c.drawString(100, 750, "测试PDF文档")
        c.drawString(100, 700, "用于测试PDF上传功能")
        c.drawString(100, 650, f"创建时间: {Path(pdf_path).stat().st_mtime}")
        c.save()
        print(f"已创建测试PDF文件: {pdf_path}")
    except ImportError:
        print("无法创建测试PDF文件，缺少reportlab库")
        print("创建一个简单的PDF占位符...")
        # 创建一个简单的PDF文件作为占位符
        with open(pdf_path, 'wb') as f:
            # 创建一个基础的PDF文件头
            f.write(b'%PDF-1.4\n')
            f.write(b'1 0 obj\n')
            f.write(b'<<\n')
            f.write(b'  /Type /Catalog\n')
            f.write(b'  /Pages 2 0 R\n')
            f.write(b'>>\n')
            f.write(b'endobj\n')
            f.write(b'2 0 obj\n')
            f.write(b'<<\n')
            f.write(b'  /Type /Pages\n')
            f.write(b'  /Kids [3 0 R]\n')
            f.write(b'  /Count 1\n')
            f.write(b'>>\n')
            f.write(b'endobj\n')
            f.write(b'3 0 obj\n')
            f.write(b'<<\n')
            f.write(b'  /Type /Page\n')
            f.write(b'  /Parent 2 0 R\n')
            f.write(b'  /MediaBox [0 0 612 792]\n')
            f.write(b'  /Contents 4 0 R\n')
            f.write(b'>>\n')
            f.write(b'endobj\n')
            f.write(b'4 0 obj\n')
            f.write(b'<<\n')
            f.write(b'  /Length 44\n')
            f.write(b'>>\n')
            f.write(b'stream\n')
            f.write(b'BT\n/F1 12 Tf\n100 700 Td\n(Test PDF File) Tj\nET\n')
            f.write(b'endstream\n')
            f.write(b'endobj\n')
            f.write(b'xref\n')
            f.write(b'0 5\n')
            f.write(b'0000000000 65535 f \n')
            f.write(b'0000000018 00000 n \n')
            f.write(b'0000000077 00000 n \n')
            f.write(b'0000000178 00000 n \n')
            f.write(b'0000000300 00000 n \n')
            f.write(b'trailer\n')
            f.write(b'<<\n')
            f.write(b'  /Size 5\n')
            f.write(b'  /Root 1 0 R\n')
            f.write(b'>>\n')
            f.write(b'startxref\n')
            f.write(b'425\n')
            f.write(b'%%EOF\n')
        print(f"已创建PDF占位符文件: {pdf_path}")

if __name__ == "__main__":
    test_upload()