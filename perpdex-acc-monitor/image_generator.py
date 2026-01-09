from PIL import Image, ImageDraw, ImageFont
from aggregator import aggregate_all_data
import os

def generate_summary_image(output_path="perp_summary.png"):
    data = aggregate_all_data()
    
    width = 1500  # 更宽，防止挤出
    height = 2700  # 更长
    bg_color = (18, 18, 18)
    text_color = (255, 255, 255)
    green = (0, 255, 128)
    red = (255, 82, 82)
    
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    try:
        time_font = ImageFont.truetype("arial.ttf", 40)
        total_label_font = ImageFont.truetype("arial.ttf", 48)
        total_value_font = ImageFont.truetype("arialbd.ttf", 72)
        italic_title_font = ImageFont.truetype("ariali.ttf", 40)
        header_font = ImageFont.truetype("arialbd.ttf", 34)
        normal_font = ImageFont.truetype("arial.ttf", 30)
        small_font = ImageFont.truetype("arial.ttf", 28)
    except:
        time_font = ImageFont.load_default()
        total_label_font = ImageFont.load_default()
        total_value_font = ImageFont.load_default()
        italic_title_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        normal_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    y = 40
    
    # 顶部时间
    draw.text((width // 2, y), data["update_time"], font=time_font, fill=text_color, anchor="mt")
    y += 100
    
    # Total Equity
    draw.text((width // 2, y), "Total Equity:", font=total_label_font, fill=text_color, anchor="mt")
    y += 70
    draw.text((width // 2, y), f"${int(round(data['Total Equity'])):,}", font=total_value_font, fill=text_color, anchor="mt")
    y += 100
    
    # Total Exposure
    draw.text((width // 2, y), "Total Exposure:", font=total_label_font, fill=text_color, anchor="mt")
    y += 70
    draw.text((width // 2, y), f"${int(round(data['Total Exposure'])):,}", font=total_value_font, fill=text_color, anchor="mt")
    y += 150
    
    # Summary by Venue
    draw.text((60, y), "***Summary by Venue***", font=italic_title_font, fill=text_color)
    y += 60
    
    venue_headers = ["Venue", "Equity", "Net Exposure", "Gross Exposure"]
    venue_col_widths = [300, 400, 400, 400]
    x = 60
    for header in venue_headers:
        draw.text((x, y), header, font=header_font, fill=text_color)
        x += venue_col_widths[venue_headers.index(header)]
    y += 60
    
    for ex in data["exchanges"]:
        venue = ex["exchange_name"]
        equity = int(round(ex["Exchange Equity"]))
        net_exposure = int(round(ex["Exchange Exposure"]))
        gross_exposure = int(round(ex["Exchange Gross Exposure"]))
        
        x = 60
        draw.text((x, y), venue, font=normal_font, fill=text_color)
        x += venue_col_widths[0]
        draw.text((x, y), f"${equity:,}", font=normal_font, fill=text_color)
        x += venue_col_widths[1]
        draw.text((x, y), f"${net_exposure:,}", font=normal_font, fill=text_color)  # 无颜色
        x += venue_col_widths[2]
        draw.text((x, y), f"${gross_exposure:,}", font=normal_font, fill=text_color)
        y += 60
    
    y += 100
    
    # Summary by Account
    draw.text((60, y), "***Summary by Account***", font=italic_title_font, fill=text_color)
    y += 60
    
    acc_headers = ["Account", "Equity", "N_Exposure", "G_Exposure"]
    acc_col_widths = [350, 350, 450, 450]  # 加宽
    x = 60
    for header in acc_headers:
        draw.text((x, y), header, font=header_font, fill=text_color)
        x += acc_col_widths[acc_headers.index(header)]
    y += 60
    
    for ex in data["exchanges"]:
        for i, acc in enumerate(ex["accounts"], 1):
            account_name = f"{ex['exchange_name']}_Acc{i:02d}"
            equity = int(round(acc["Equity"]))
            net_exposure = int(round(acc["Net Exposure"]))
            net_leverage = acc["Net Leverage"]
            gross_exposure = int(round(acc["Gross Exposure"]))
            gross_leverage = acc["Gross Leverage"]
            
            n_str = f"${net_exposure:,} ({net_leverage:.2f}x)"
            g_str = f"${gross_exposure:,} ({gross_leverage:.2f}x)"
            
            x = 60
            draw.text((x, y), account_name, font=normal_font, fill=text_color)
            x += acc_col_widths[0]
            draw.text((x, y), f"${equity:,}", font=normal_font, fill=text_color)
            x += acc_col_widths[1]
            draw.text((x, y), n_str, font=normal_font, fill=text_color)
            x += acc_col_widths[2]
            draw.text((x, y), g_str, font=normal_font, fill=text_color)
            
            y += 60
    
    y += 100
    
    # Positions
    draw.text((60, y), "***Positions***", font=italic_title_font, fill=text_color)
    y += 60
    
    pos_headers = ["Account", "Instrument", "Size", "Exposure", "Liq.price"]
    pos_col_widths = [350, 300, 150, 300, 300]
    x = 60
    for header in pos_headers:
        draw.text((x, y), header, font=header_font, fill=text_color)
        x += pos_col_widths[pos_headers.index(header)]
    y += 60
    
    for ex in data["exchanges"]:
        for i, acc in enumerate(ex["accounts"], 1):
            account_name = f"{ex['exchange_name']}_Acc{i:02d}"
            for pos in acc["positions"]:
                instrument = pos["Instrument"]
                size = pos["Size"]
                size_color = green if size > 0 else red
                exposure = int(round(pos["Exposure"]))
                liq = pos["Liq.price"]
                
                x = 60
                draw.text((x, y), account_name, font=normal_font, fill=text_color)
                x += pos_col_widths[0]
                draw.text((x, y), instrument, font=normal_font, fill=text_color)
                x += pos_col_widths[1]
                draw.text((x, y), str(size), font=normal_font, fill=size_color)
                x += pos_col_widths[2]
                draw.text((x, y), f"${exposure:,}", font=normal_font, fill=text_color)
                x += pos_col_widths[3]
                draw.text((x, y), f"{liq:.2f}", font=normal_font, fill=text_color)
                
                y += 50
    
    img.save(output_path)
    print(f"图片生成完成: {os.path.abspath(output_path)}")

if __name__ == "__main__":
    generate_summary_image("perp_summary.png")
