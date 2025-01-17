from collections import Counter

from PyQt5.QtCore import QFile, QTextStream, QIODevice

import sys

sys.path.append('.')

from app.DataBase import msg_db, MsgType
from pyecharts import options as opts
from pyecharts.charts import WordCloud, Calendar, Bar, Line
from app.resources import resource_rc

import tkinter as tk
import os
from tkinter import messagebox
import shutil

var = resource_rc.qt_resource_name
charts_width = 800
charts_height = 450
wordcloud_width = 780
wordcloud_height = 720

class StopwordsWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("屏蔽词管理")
        self.geometry("250x170")

        # File paths
        original_stopwords_file = os.path.abspath('./app/data/stopwords.txt')
        default_stopwords_file = os.path.abspath('./app/data/default_stopwords.txt')

        # Read existing stopwords from the original file
        with open(original_stopwords_file, "r", encoding="utf-8") as original_stopword_file:
            self.original_stopwords = set(original_stopword_file.read().splitlines())

        # Create a replicate of the original stopwords file as the default file
        if not os.path.exists(default_stopwords_file):
            shutil.copy(original_stopwords_file, default_stopwords_file)

        # UI elements
        self.label = tk.Label(self, text="输入你想添加的屏蔽词:")
        self.label.pack(pady=10)

        self.user_input = tk.StringVar()
        entry = tk.Entry(self, textvariable=self.user_input)
        entry.pack(pady=10)

        self.add_button = tk.Button(self, text="添加屏蔽词", command=self.add_stopwords)
        self.add_button.pack(pady=5)

        self.undo_button = tk.Button(self, text="撤销", command=self.undo_stopwords)
        self.undo_button.pack(pady=5)

    def add_stopwords(self):
        original_stopwords_file = os.path.abspath('./app/data/stopwords.txt')
        
        user_input = self.user_input.get()
        word_list = user_input.split()

        # Check if each word already exists in the original file before appending
        duplicates = [word for word in word_list if word in self.original_stopwords]
        if duplicates:
            message = f"以下屏蔽词已存在于原始文件中: {', '.join(duplicates)}"
            messagebox.showinfo("重复词汇", message)
        else:
            # Update the original stopwords set with new words
            self.original_stopwords.update(word_list)

            # Write the updated original stopwords set back to the file
            with open(original_stopwords_file, 'w', encoding="utf-8") as original_stopword_file:
                original_stopword_file.write("\n".join(self.original_stopwords))

            messagebox.showinfo("Success", "屏蔽词已添加")

    def undo_stopwords(self):
        try:
            # Revert the stopwords file to its original state
            original_stopwords_file = os.path.abspath('./app/data/stopwords.txt')
            default_stopwords_file = os.path.abspath('./app/data/default_stopwords.txt')
            shutil.copy(default_stopwords_file, original_stopwords_file)
            messagebox.showinfo("Undo", "屏蔽词已还原至原始状态")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

def wordcloud(wxid, is_Annual_report=False, year='2023', who='1'):
    import jieba
    txt_messages = msg_db.get_messages_by_type(wxid, MsgType.TEXT, is_Annual_report, year)
    if not txt_messages:
        return {
            'chart_data': None,
            'keyword': "没有聊天你想分析啥",
            'max_num': "0",
            'dialogs': []
        }
    # text = ''.join(map(lambda x: x[7], txt_messages))
    text = ''.join(map(lambda x: x[7] if x[4] == int(who) else '', txt_messages))  # 1“我”说的话，0“Ta”说的话

    total_msg_len = len(text)
    # 使用jieba进行分词，并加入停用词
    words = jieba.cut(text)
    # 统计词频
    word_count = Counter(words)
    # 过滤停用词
    stopwords_file = './app/data/stopwords.txt'

    stopwords_window = StopwordsWindow()
    stopwords_window.mainloop()
    
    try:
        with open(stopwords_file, "r", encoding="utf-8") as stopword_file:
            stopwords = set(stopword_file.read().splitlines())

    except:
        file = QFile(':/data/stopwords.txt')
        if file.open(QIODevice.ReadOnly | QIODevice.Text):
            stream = QTextStream(file)
            stream.setCodec('utf-8')
            content = stream.readAll()
            file.close()
            stopwords = set(content.splitlines())
    filtered_word_count = {word: count for word, count in word_count.items() if len(word) > 1 and word not in stopwords}

    # 转换为词云数据格式
    data = [(word, count) for word, count in filtered_word_count.items()]
    # text_data = data
    data.sort(key=lambda x: x[1], reverse=True)

    text_data = data[:100] if len(data) > 100 else data
    # 创建词云图
    keyword, max_num = text_data[0]
    w = (
        WordCloud(init_opts=opts.InitOpts(width=f"{wordcloud_width}px", height=f"{wordcloud_height}px"))
        .add(series_name="聊天文字", data_pair=text_data, word_size_range=[5, 40])
    )
    # return w.render_embed()
    return {
        'chart_data': w.dump_options_with_quotes(),
        'keyword': keyword,
        'max_num': str(max_num),
        'dialogs': msg_db.get_messages_by_keyword(wxid, keyword, num=5, max_len=12)
    }


def calendar_chart(wxid, is_Annual_report=False, year='2023'):
    calendar_data = msg_db.get_messages_by_days(wxid, is_Annual_report, year)

    if not calendar_data:
        return False
    min_ = min(map(lambda x: x[1], calendar_data))
    max_ = max(map(lambda x: x[1], calendar_data))
    start_date_ = calendar_data[0][0]
    end_date_ = calendar_data[-1][0]
    print(start_date_, '---->', end_date_)
    if is_Annual_report:
        calendar_days = year
        calendar_title = f'{year}年聊天情况'
    else:
        calendar_days = (start_date_, end_date_)
        calendar_title = '和Ta的聊天情况'
    c = (
        Calendar(init_opts=opts.InitOpts(width=f"{charts_width}px", height=f"{charts_height}px"))
        .add(
            "",
            calendar_data,
            calendar_opts=opts.CalendarOpts(range_=calendar_days)
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title=calendar_title),
            visualmap_opts=opts.VisualMapOpts(
                max_=max_,
                min_=min_,
                orient="horizontal",
                # is_piecewise=True,
                # pos_top="200px",
                pos_bottom="0px",
                pos_left="0px",
            ),
            legend_opts=opts.LegendOpts(is_show=False)
        )
    )
    return {
        'chart_data': c
    }


def month_count(wxid, is_Annual_report=False, year='2023'):
    """
    每月聊天条数
    """
    msg_data = msg_db.get_messages_by_month(wxid, is_Annual_report, year)
    y_data = list(map(lambda x: x[1], msg_data))
    x_axis = list(map(lambda x: x[0], msg_data))
    m = (
        Bar(init_opts=opts.InitOpts(width=f"{charts_width}px", height=f"{charts_height}px"))
        .add_xaxis(x_axis)
        .add_yaxis("消息数量", y_data,
                   label_opts=opts.LabelOpts(is_show=False),
                   itemstyle_opts=opts.ItemStyleOpts(color="skyblue"),
                   )
        .set_global_opts(
            title_opts=opts.TitleOpts(title="逐月统计", subtitle=None),
            datazoom_opts=opts.DataZoomOpts(),
            toolbox_opts=opts.ToolboxOpts(),
            visualmap_opts=opts.VisualMapOpts(
                min_=min(y_data),
                max_=max(y_data),
                dimension=1,  # 根据第2个维度（y 轴）进行映射
                is_piecewise=False,  # 是否分段显示
                range_color=["#66ccff", "#003366"],  # 设置颜色范围
                type_="color",
                pos_right="0%",
            ),
        )
    )

    return {
        'chart_data': m
    }


def hour_count(wxid, is_Annual_report=False, year='2023'):
    """
    小时计数聊天条数
    """
    msg_data = msg_db.get_messages_by_hour(wxid, is_Annual_report, year)
    print(msg_data)
    y_data = list(map(lambda x: x[1], msg_data))
    x_axis = list(map(lambda x: x[0], msg_data))
    h = (
        Line(init_opts=opts.InitOpts(width=f"{charts_width}px", height=f"{charts_height}px"))
        .add_xaxis(xaxis_data=x_axis)
        .add_yaxis(
            series_name="聊天频率",
            y_axis=y_data,
            markpoint_opts=opts.MarkPointOpts(
                data=[
                    opts.MarkPointItem(type_="max", name="最大值"),
                    opts.MarkPointItem(type_="min", name="最小值", value=int(10)),
                ]
            ),
            markline_opts=opts.MarkLineOpts(
                data=[opts.MarkLineItem(type_="average", name="平均值")]
            ),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title="聊天时段", subtitle=None),
            # datazoom_opts=opts.DataZoomOpts(),
            # toolbox_opts=opts.ToolboxOpts(),
        )
        .set_series_opts(
            label_opts=opts.LabelOpts(
                is_show=False
            )
        )
    )

    return {
        'chart_data': h
    }


class Analysis:
    pass


if __name__ == '__main__':
    msg_db.init_database(path='../DataBase/Msg/MSG.db')
    # w = wordcloud('wxid_0o18ef858vnu22')
    w_data = wordcloud('wxid_27hqbq7vx5hf22', True, '2023')
    # print(w_data)
    # w['chart_data'].render("./data/聊天统计/wordcloud.html")
    c = calendar_chart('wxid_27hqbq7vx5hf22', False, '2023')
    c['chart_data'].render("./data/聊天统计/calendar.html")
    # print('c:::', c)
    m = month_count('wxid_27hqbq7vx5hf22', False, '2023')
    m['chart_data'].render("./data/聊天统计/month_num.html")
    h = hour_count('wxid_27hqbq7vx5hf22')
    h['chart_data'].render("./data/聊天统计/hour_count.html")
