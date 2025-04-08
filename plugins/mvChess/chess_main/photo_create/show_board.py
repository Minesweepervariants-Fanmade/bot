from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import os

main_path=os.getcwd()+"/"
main_path = Path(__file__).parent.__str__()+"\\"

def generate_grid_image(
    data: list[list],
    mini_data:list[list],
    dye:list[list[bool]],
    font_path: str = main_path+"CopperplateCC-Heavy.ttf",
    output_path: str = main_path+"demo.png",
    font_size: int = 100
):
    """
    生成黑底白框网格图片
    :param data: 二维文本列表(如：[["A1", "B1"], ["A2", "B2"]])
    :param font_path: 字体文件路径
    :param output_path: 输出图片路径(默认grid.png)
    :param font_size: 字体大小(默认20)
    :param padding: 单元格内边距(默认10)
    :param grid_width: 网格线宽度(默认1像素)
    """
    padding=font_size//3
    grid_width=font_size//20
    # 参数校验
    if not data or not isinstance(data, list) or not all(isinstance(row, list) for row in data):
        raise ValueError("无效的二维数据格式")
    
    rows = len(data)
    cols = len(data[0]) if rows > 0 else 0
    for row in data:
        if len(row) != cols:
            raise ValueError("所有行的列数必须一致")

    # 加载字体
    try:
        font = ImageFont.truetype(font_path, font_size)
        small_font = ImageFont.truetype(font_path, (font_size*4)//5)
        half_font = ImageFont.truetype(font_path, (font_size*2)//3)
        P_half_font = ImageFont.truetype(font_path, (font_size*2)//3)
        mini_font = ImageFont.truetype(font_path, font_size//3)
    except IOError:
        raise ValueError(f"字体文件加载失败: {font_path}")

    # 计算最大文本尺寸
    draw = ImageDraw.Draw(Image.new("RGB", (0, 0)))
    max_text_w, max_text_h = 0, 0
    for row in data:
        for text in row:
            bbox = draw.textbbox((0, 0), str(text), font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            max_text_w = max(max_text_w, text_w)
            max_text_h = max(max_text_h, text_h)

    bbox = draw.textbbox((0, 0), str('5'), font=font)
    max_text_w, max_text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]

    # 计算单元格尺寸
    cell_width = max_text_w + 2 * padding
    cell_height = max_text_h + 2 * padding

    # 计算画布尺寸
    total_width = grid_width * (cols + 1) + cell_width * cols
    total_height = grid_width * (rows + 1) + cell_height * rows

    # 创建画布
    image = Image.new("RGB", (total_width, total_height), color="black")
    draw = ImageDraw.Draw(image)

    # 绘制网格线
    for j in range(cols + 1):
        x = j * (cell_width + grid_width)
        draw.line([(x, 0), (x, total_height)], fill="white", width=grid_width)
    
    for i in range(rows + 1):
        y = i * (cell_height + grid_width)
        draw.line([(0, y), (total_width, y)], fill="white", width=grid_width)
    
    for i in range(cols):
        for j in range(rows):
            x = i * (cell_width + grid_width)
            y = j * (cell_height + grid_width)
            if dye[j][i]:
                draw.rectangle([(x+(grid_width+1)//2,y+(grid_width+1)//2),(x+cell_width+(grid_width)//2,y+cell_height+(grid_width)//2)], fill="gray", width=grid_width)

    # 填充文本
    for i in range(rows):
        for j in range(cols):
            text = str(data[i][j])
            cell_x = grid_width + j * (cell_width + grid_width)
            cell_y = grid_width + i * (cell_height + grid_width)-padding

            if str(mini_data[i][j])=='1E\'' and text!='0':
                if '-' in text:
                    bbox = draw.textbbox((0, 0), text[1:], font=small_font)
                else:
                    bbox = draw.textbbox((0, 0), text, font=small_font)
            elif '_' in text:
                bbox = draw.textbbox((0, 0), '+', font=half_font)
            elif '√' in text:
                TS=text.split('√')
                text=TS[0]+'+'+TS[1]
                bbox = draw.textbbox((0, 0), TS[0]+' '+TS[1], font=P_half_font)
            else:
                bbox = draw.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            
            x = cell_x + (cell_width - text_w) // 2
            y = cell_y + (cell_height - text_h) // 2
            if text=='F':
                #draw.text((x, y), text, font=font, fill="yellow")
                png_image = Image.open(main_path+"Flag.png").convert("RGBA")
                png_image.thumbnail((cell_width+padding//2, cell_height+padding//2))
                image.paste(png_image, (x-padding-padding//6, y-padding//4), mask=png_image)
            elif text=='!':
                draw.text((x, y), text, font=font, fill="yellow")
            elif '+' in text:
                png_image = Image.open(main_path+"sqrt.png").convert("RGBA")
                png_image.thumbnail((text_w//len(text)*2+grid_width, text_w//len(text)*2+grid_width))
                image.paste(png_image, (x-padding*3//4+(len(TS[0]))*text_w//len(text)-grid_width//2, y+padding//3-grid_width), mask=png_image)
                draw.text((x, y), TS[0]+' '+TS[1], font=P_half_font, fill="white")
            elif '_' in text:
                text_list=text.split('_')
                if len(text_list)==2:
                    if text_list[0]=='1':
                        draw.text((x-(padding*4)//5, y), text_list[0], font=half_font, fill="white")
                    else:
                        draw.text((x-(padding), y), text_list[0], font=half_font, fill="white")
                    if text_list[1]=='1':
                        draw.text((x+(padding), y), text_list[1], font=half_font, fill="white")
                    else:
                        draw.text((x+(padding*4)//5, y), text_list[1], font=half_font, fill="white")
                elif len(text_list)==3:
                    if text_list[0]=='1':
                        draw.text((x-(padding*4)//5, y-(padding)), text_list[0], font=half_font, fill="white")
                    else:
                        draw.text((x-(padding), y-(padding)), text_list[0], font=half_font, fill="white")
                    if text_list[1]=='1':
                        draw.text((x+(padding), y-(padding)), text_list[1], font=half_font, fill="white")
                    else:
                        draw.text((x+(padding*4)//5, y-(padding)), text_list[1], font=half_font, fill="white")
                    if text_list[2]=='1':
                        draw.text((x, y+(padding)), text_list[2], font=half_font, fill="white")
                    else:
                        draw.text((x-padding//5, y+(padding)), text_list[2], font=half_font, fill="white")
                elif len(text_list)==4:
                    if text_list[0]=='1':
                        draw.text((x-(padding*4)//5, y-(padding)), text_list[0], font=half_font, fill="white")
                    else:
                        draw.text((x-(padding), y-(padding)), text_list[0], font=half_font, fill="white")
                    if text_list[1]=='1':
                        draw.text((x+(padding), y-(padding)), text_list[1], font=half_font, fill="white")
                    else:
                        draw.text((x+(padding*4)//5, y-(padding)), text_list[1], font=half_font, fill="white")
                    if text_list[2]=='1':
                        draw.text((x-(padding*4)//5, y+(padding)), text_list[2], font=half_font, fill="white")
                    else:
                        draw.text((x-(padding), y+(padding)), text_list[2], font=half_font, fill="white")
                    if text_list[3]=='1':
                        draw.text((x+(padding), y+(padding)), text_list[3], font=half_font, fill="white")
                    else:
                        draw.text((x+(padding*4)//5, y+(padding)), text_list[3], font=half_font, fill="white")
            elif str(mini_data[i][j])=='1E\'' and text!='0':
                if text[0]=='-':
                    text=text[1:]
                    png_image=Image.open(main_path+"double_horizontal_arrow.png").convert("RGBA")
                    png_image.thumbnail((cell_width-padding, cell_height-padding))
                    image.paste(png_image, (x-(padding*8)//5+text_w//2, y-grid_width), mask=png_image)
                    draw.text((x, y+(padding*2)//3), text, font=small_font, fill="white")
                else:
                    png_image=Image.open(main_path+"double_vertical_arrow.png").convert("RGBA")
                    png_image.thumbnail((cell_width-padding, cell_height-padding))
                    image.paste(png_image, (x-padding+text_w//10, y+grid_width), mask=png_image)
                    draw.text((x+(padding)//2, y), text, font=small_font, fill="white")
            else:
                draw.text((x, y), text, font=font, fill="white")
        
    for i in range(rows):
        for j in range(cols):
            text = str(mini_data[i][j])
            cell_x = j * (cell_width + grid_width)
            cell_y = i * (cell_height + grid_width)
            
            bbox = draw.textbbox((0, 0), text, font=mini_font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            
            x = cell_x + (cell_width - text_w)
            y = cell_y + (cell_height - text_h)-padding//3
            if text=='1E\'' and str(data[i][j])!='0':
                continue
            else:
                draw.text((x, y), text, font=mini_font, fill="white")

    image.save(output_path)

# 使用示例
if __name__ == "__main__":
    N=8
    sample_data = [['' for _ in range(N)] for _ in range(N)]
    sample_data_mini = [['' for _ in range(N)] for _ in range(N)]
    dye=[[False for _ in range(N)] for _ in range(N)]
    for y in range(N):
        for x in range(N):
            if (x+y) & 1:
                dye[y][x]=True
    
    '''
    sample_data[4][4]='F'
    sample_data[3][3]='?'
    sample_data[3][5]='?'
    sample_data[5][3]='?'
    sample_data[5][5]='?'
    dye[3][3]=True
    dye[3][5]=True
    dye[5][3]=True
    dye[5][5]=True
    sample_data[7][0]='2'
    sample_data[6][0]='?'
    sample_data[7][2]='?'
    dye[7][2]=True
    sample_data[11][0]='3'
    sample_data[11][2]='?'
    dye[11][2]=True
    sample_data[15][0]='4'
    sample_data[15][1]='?'
    sample_data[14][1]='F'
    sample_data[16][1]='F'
    sample_data[14][0]='F'
    sample_data[16][0]='F'
    dye[15][1]=True
    dye[14][1]=True
    dye[16][1]=True
    dye[14][0]=True
    dye[16][0]=True
    sample_data[9][7]='5'
    sample_data[9][9]='?'
    sample_data[9][5]='?'
    sample_data[7][7]='?'
    sample_data[11][7]='?'
    dye[9][9]=True
    dye[9][5]=True
    dye[7][7]=True
    dye[11][7]=True
    sample_data[15][7]='6'
    sample_data[14][8]='F'
    sample_data[16][8]='F'
    sample_data[14][6]='F'
    sample_data[16][6]='F'
    dye[14][8]=True
    dye[16][8]=True
    dye[14][6]=True
    dye[16][6]=True
    sample_data[3][7]='!'
    sample_data[3][9]='!'
    sample_data[2][8]='?'
    sample_data[4][8]='?'
    dye[2][8]=True
    dye[4][8]=True
    sample_data[2][14]='3'
    sample_data[2][13]='?'
    sample_data[3][13]='?'
    sample_data[3][14]='?'
    sample_data[3][15]='?'
    sample_data[1][12]='F'
    sample_data[1][13]='F'
    sample_data[1][15]='F'
    sample_data[1][16]='?'
    dye[1][16]=True
    sample_data[7][15]='2'
    sample_data[7][14]='4'
    sample_data[7][16]='?'
    sample_data[7][12]='?'
    sample_data[5][14]='?'
    sample_data[9][14]='?'
    dye[7][16]=True
    dye[7][12]=True
    dye[5][14]=True
    dye[9][14]=True
    sample_data[12][15]='2'
    sample_data[12][14]='3'
    sample_data[13][15]='?'
    sample_data[12][12]='?'
    dye[12][12]=True
    sample_data[16][15]='6'
    sample_data[16][13]='5'
    sample_data[15][16]='F'
    sample_data[17][16]='F'
    sample_data[15][14]='F'
    sample_data[17][14]='F'
    sample_data[15][13]='?'
    sample_data[17][13]='?'
    dye[15][13]=True
    dye[17][13]=True
    sample_data[0][0]='?'
    sample_data[0][2]='?'
    sample_data[2][0]='?'
    sample_data[0][1]='>0'
    sample_data[1][0]='>0'
    sample_data[1][1]='F'
    dye[1][1]=True
    '''

    generate_grid_image(
        data=sample_data,
        mini_data=sample_data_mini,
        dye=dye,
        font_path=main_path+"CopperplateCC-Heavy.ttf",  # 替换为你的字体文件路径
        output_path=main_path+"demo.png",
        font_size=120
    )