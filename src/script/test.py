from src.utils.extractor import Extractor
import re
table_doc = """
<table class="cjsj_tab2">
                            <tbody><tr class="s_blue"> <th width="70px">时间</th> <th width="60px">国家地区</th> <th width="120px">地点</th> <th width="80px">重要性</th> <th>事件</th> </tr>
                                        <tr>                    <td class="tab_time" width="70">待定</td>
                    <td width="135"><div class="flag_bb"><div class="c_usa circle_flag"></div><span>美国</span></div></td>
                    <td>德克萨斯州</td>
                    <td> <img src="/Public/images/star_1.png"></td>
                    <td class="tab_font">美国达拉斯联储主席卡普兰(Robert Steven Kaplan)发表讲话。</td>
                    </tr>                        <tr>                    <td class="tab_time" width="70">待定</td>
                    <td width="135"><div class="flag_bb"><div class="c_usa circle_flag"></div><span>美国</span></div></td>
                    <td>华盛顿特区</td>
                    <td> <img src="/Public/images/star_2.png"></td>
                    <td class="tab_font">美国总统特朗普(Donald John Trump)会见澳大利亚总理莫里森(Scott Morrison)。</td>
                    </tr>                        <tr>                    <td class="tab_time" width="70">14:30</td>
                    <td width="135"><div class="flag_bb"><div class="c_sweden circle_flag"></div><span>瑞典</span></div></td>
                    <td>马尔默</td>
                    <td> <img src="/Public/images/star_1.png"></td>
                    <td class="tab_font">瑞典央行副行长扬松(Per Jansson)发表讲话。</td>
                    </tr><tr class="red_color_s">
                                        <td class="tab_time" width="70">20:15</td>
                    <td width="135"><div class="flag_bb"><div class="c_switzerland circle_flag"></div><span>瑞士</span></div></td>
                    <td>---</td>
                    <td> <img src="/Public/images/star_3.png"></td>
                    <td class="tab_font">FOMC永久票委、纽约联储主席威廉姆斯(John Williams)在瑞士央行举办的会议上发表讲话。</td>
                    </tr><tr class="red_color_s">
                                        <td class="tab_time" width="70">23:20</td>
                    <td width="135"><div class="flag_bb"><div class="c_usa circle_flag"></div><span>美国</span></div></td>
                    <td>纽约</td>
                    <td> <img src="/Public/images/star_3.png"></td>
                    <td class="tab_font">2019年FOMC票委、波士顿联储主席罗森格伦(Eric Rosengren)在纽约大学发表讲话。</td>
                    </tr>            <tr><td colspan="9" style="font-weight:bold;color:#1f2e5b"><div onclick="getEventMore(this)" style="cursor:pointer;text-decoration:underline;">查看完整交易日大事</div></td>        </tr></tbody></table>
"""
for rate in range(4):
    table_doc = table_doc.replace('<img src="/Public/images/star_' + str(rate) + '.png">', '<span>' + str(rate) + '</span>')
extractor = Extractor(table_doc)

extractor.parse()
result = extractor.return_list()

print(result)