import pygame
import time
import random

# 初始化pygame
pygame.init()

# 定义颜色
white = (255, 255, 255)
yellow = (255, 255, 102)
black = (0, 0, 0)
red = (213, 50, 80)
green = (0, 255, 0)
blue = (50, 153, 213)

# 设置窗口大小
dis_width = 800
dis_height = 600

# 创建游戏窗口
dis = pygame.display.set_mode((dis_width, dis_height))
pygame.display.set_caption('贪吃蛇游戏')

# 设置时钟
clock = pygame.time.Clock()

# 蛇的大小和速度
snake_block = 10
snake_speed = 15

# 设置字体
# 设置字体（修改为支持中文的字体）
# 需要准备一个支持中文的字体文件，如simhei.ttf
font_style = pygame.font.Font("simhei.ttf", 25)
score_font = pygame.font.Font("simhei.ttf", 35)

def our_snake(snake_block, snake_list, is_player=True):
    # 绘制蛇身
    for x in snake_list[:-1]:
        # 玩家蛇为黑色，AI蛇为灰色
        color = black if is_player else (128, 128, 128)
        pygame.draw.rect(dis, color, [x[0], x[1], snake_block, snake_block])
    
    # 绘制蛇头
    head = snake_list[-1]
    if is_player:
        # 玩家蛇头样式
        pygame.draw.rect(dis, red, [head[0], head[1], snake_block, snake_block])
        eye_size = snake_block // 4
        pygame.draw.circle(dis, white, (head[0] + snake_block//4, head[1] + snake_block//4), eye_size)
        pygame.draw.circle(dis, white, (head[0] + 3*snake_block//4, head[1] + snake_block//4), eye_size)
    else:
        # AI蛇头样式
        pygame.draw.rect(dis, green, [head[0], head[1], snake_block, snake_block])
        # 在AI蛇头上画一个X
        pygame.draw.line(dis, black, (head[0], head[1]), 
                        (head[0] + snake_block, head[1] + snake_block), 2)
        pygame.draw.line(dis, black, (head[0] + snake_block, head[1]), 
                        (head[0], head[1] + snake_block), 2)

def check_collision(snake_head, other_snakes):
    # 检查蛇头是否撞到其他蛇身，使用精确比较
    for snake in other_snakes:
        for segment in snake['list'][:-1]:  # 不包括蛇头
            if snake_head[0] == segment[0] and snake_head[1] == segment[1]:
                return True
    return False

def drop_food(snake_list, foods):
    # 蛇死亡时掉落食物，确保食物位置对齐
    for segment in snake_list:
        x = round(segment[0] / 10.0) * 10.0
        y = round(segment[1] / 10.0) * 10.0
        foods.append([x, y])

def message(msg, color):
    mesg = font_style.render(msg, True, color)
    dis.blit(mesg, [dis_width/6, dis_height/3])
def ai_snake_move(snake, food, dis_width, dis_height, snake_block):
    head = snake[-1]
    x_dir = 0
    y_dir = 0

    # 先判断是否靠近墙壁
    if head[0] < snake_block and food[0] < head[0]:
        x_dir = snake_block  # 避免撞墙
    elif head[0] > dis_width - 2 * snake_block and food[0] > head[0]:
        x_dir = -snake_block  # 避免撞墙
    elif head[1] < snake_block and food[1] < head[1]:
        y_dir = snake_block  # 避免撞墙
    elif head[1] > dis_height - 2 * snake_block and food[1] > head[1]:
        y_dir = -snake_block  # 避免撞墙
    else:
        if head[0] < food[0]:
            x_dir = snake_block
        elif head[0] > food[0]:
            x_dir = -snake_block
        elif head[1] < food[1]:
            y_dir = snake_block
        else:
            y_dir = -snake_block

    # 避免撞到自己
    next_head = [head[0] + x_dir, head[1] + y_dir]
    if next_head in snake[:-1]:
        # 尝试换个方向
        if x_dir != 0:
            x_dir = 0
            if head[1] < food[1]:
                y_dir = snake_block
            else:
                y_dir = -snake_block
        else:
            y_dir = 0
            if head[0] < food[0]:
                x_dir = snake_block
            else:
                x_dir = -snake_block
    return x_dir, y_dir
def gameLoop():
    # Indent the code inside the function
    game_over = False
    game_close = False
    paused = False  # 新增暂停状态变量
    player_death_time = None  # 记录玩家死亡时间
    ai_death_times = {}  # 记录AI蛇死亡时间
    # 初始化玩家蛇，确保位置是10的倍数
    x1 = round(dis_width / 2 / 10.0) * 10.0
    y1 = round(dis_height / 2 / 10.0) * 10.0
    x1_change = 0
    y1_change = 0
    snake_List = [[x1, y1]]
    Length_of_snake = 1
    # 初始化两个AI蛇，确保位置是10的倍数
    ai_snakes = [
        {'x': round(dis_width / 4 / 10.0) * 10.0, 
         'y': round(dis_height / 4 / 10.0) * 10.0, 
         'x_change': 0, 'y_change': 0, 
         'list': [[round(dis_width / 4 / 10.0) * 10.0, 
                   round(dis_height / 4 / 10.0) * 10.0]], 
         'length': 1, 'dead': False},
        {'x': round(3 * dis_width / 4 / 10.0) * 10.0, 
         'y': round(3 * dis_height / 4 / 10.0) * 10.0, 
         'x_change': 0, 'y_change': 0,
         'list': [[round(3 * dis_width / 4 / 10.0) * 10.0, 
                   round(3 * dis_height / 4 / 10.0) * 10.0]], 
         'length': 1, 'dead': False}
    ]
    # 初始化食物，数量为蛇的数量+1
    foods = []
    for _ in range(len(ai_snakes) + 2):  # 玩家蛇 + 2个AI蛇 + 1
        foods.append([
            round(random.randrange(0, dis_width - snake_block) / 10.0) * 10.0,
            round(random.randrange(0, dis_height - snake_block) / 10.0) * 10.0
        ])
    while not game_over:
        current_time = time.time()
        # 先填充背景色
        dis.fill(blue)
        # 绘制所有食物
        for food in foods:
            pygame.draw.rect(dis, green, [food[0], food[1], snake_block, snake_block])
        # 绘制玩家蛇
        our_snake(snake_block, snake_List, is_player=True)
        # 绘制AI蛇
        for ai in ai_snakes:
            if not ai['dead']:
                our_snake(snake_block, ai['list'], is_player=False)
        # 更新屏幕显示
        pygame.display.update()
        # 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True
            if event.type == pygame.KEYDOWN:
                # 添加暂停功能
                if event.key == pygame.K_t:
                    paused = not paused
                if not paused:  # 只有在未暂停时才处理方向键
                    if event.key == pygame.K_LEFT and x1_change <= 0:
                        x1_change = -snake_block
                        y1_change = 0
                    elif event.key == pygame.K_RIGHT and x1_change >= 0:
                        x1_change = snake_block
                        y1_change = 0
                    elif event.key == pygame.K_UP and y1_change <= 0:
                        y1_change = -snake_block
                        x1_change = 0
                    elif event.key == pygame.K_DOWN and y1_change >= 0:
                        y1_change = snake_block
                        x1_change = 0
        if not paused:  # 只有在未暂停时才更新游戏状态
            # 更新玩家蛇位置
            x1 += x1_change
            y1 += y1_change
            # 玩家蛇吃食物检测
            for food in foods[:]:
                if x1 == food[0] and y1 == food[1]:
                    foods.remove(food)
                    foods.append([
                        round(random.randrange(0, dis_width - snake_block) / 10.0) * 10.0,
                        round(random.randrange(0, dis_height - snake_block) / 10.0) * 10.0
                    ])
                    Length_of_snake += 1
                    break  # 每次只吃一个食物
            # AI蛇吃食物检测
            for ai in ai_snakes:
                if not ai['dead']:
                    for food in foods[:]:
                        if ai['x'] == food[0] and ai['y'] == food[1]:
                            foods.remove(food)
                            foods.append([
                                round(random.randrange(0, dis_width - snake_block) / 10.0) * 10.0,
                                round(random.randrange(0, dis_height - snake_block) / 10.0) * 10.0
                            ])
                            ai['length'] += 1
                            break  # 每次只吃一个食物
            # 更新玩家蛇身
            snake_Head = [x1, y1]
            snake_List.append(snake_Head)
            if len(snake_List) > Length_of_snake:
                del snake_List[0]
            # 更新AI蛇位置
            for ai in ai_snakes:
                if not ai['dead']:
                    # 找到最近的食物
                    nearest_food = min(foods, key=lambda food: 
                        abs(ai['x'] - food[0]) + abs(ai['y'] - food[1]))
                    
                    # 更新移动方向
                    ai['x_change'], ai['y_change'] = ai_snake_move(ai['list'], nearest_food, dis_width, dis_height, snake_block)
                    ai['x'] += ai['x_change']
                    ai['y'] += ai['y_change']
                    
                    # 穿墙逻辑
                    if ai['x'] >= dis_width:
                        ai['x'] = 0
                    elif ai['x'] < 0:
                        ai['x'] = dis_width - snake_block
                    if ai['y'] >= dis_height:
                        ai['y'] = 0
                    elif ai['y'] < 0:
                        ai['y'] = dis_height - snake_block
                    
                    # 更新AI蛇身
                    ai_head = [ai['x'], ai['y']]
                    ai['list'].append(ai_head)
                    if len(ai['list']) > ai['length']:
                        del ai['list'][0]
            # 穿墙逻辑
            if x1 >= dis_width:
                x1 = 0
            elif x1 < 0:
                x1 = dis_width - snake_block
            if y1 >= dis_height:
                y1 = 0
            elif y1 < 0:
                y1 = dis_height - snake_block
            # 玩家蛇碰撞检测
            # 检查是否撞到自己，排除蛇头刚移动到新位置时的误判
            if len(snake_List) > 2:
                for segment in snake_List[:-2]:
                    if segment == snake_Head:
                        game_close = True
                        player_death_time = current_time
                        drop_food(snake_List, foods)
                        break
            # 检查是否撞到AI蛇
            if not game_close:
                for ai in ai_snakes:
                    if not ai['dead'] and check_collision(snake_Head, [ai]):
                        game_close = True
                        player_death_time = current_time
                        drop_food(snake_List, foods)
                        break
            # AI蛇碰撞检测
            for ai in ai_snakes:
                if not ai['dead']:
                    # 先检查是否撞到其他AI蛇
                    for other_ai in ai_snakes:
                        if ai != other_ai and not other_ai['dead'] and len(other_ai['list']) > 1:
                            if check_collision(ai['list'][-1], [other_ai]):
                                ai['dead'] = True
                                drop_food(ai['list'], foods)
                                ai_death_times[ai_snakes.index(ai)] = current_time
                                break
                    
                    # 检查是否撞到自己（长度大于1时才检测）
                    if len(ai['list']) > 2:
                        for segment in ai['list'][:-2]:
                            if segment == ai['list'][-1]:
                                ai['dead'] = True
                                drop_food(ai['list'], foods)
                                ai_death_times[ai_snakes.index(ai)] = current_time
                                break
                    
                    # 最后检查是否撞到玩家蛇
                    if len(snake_List) > 1:
                        if check_collision(ai['list'][-1], [{'list': snake_List}]):
                            ai['dead'] = True
                            drop_food(ai['list'], foods)
                            ai_death_times[ai_snakes.index(ai)] = current_time
            # AI蛇复活逻辑
            for i, ai in enumerate(ai_snakes):
                if ai['dead'] and current_time - ai_death_times[i] >= 5:
                    ai['x'] = round(random.randrange(0, dis_width - snake_block) / 10.0) * 10.0
                    ai['y'] = round(random.randrange(0, dis_height - snake_block) / 10.0) * 10.0
                    ai['x_change'] = 0
                    ai['y_change'] = 0
                    ai['list'] = [[ai['x'], ai['y']]]
                    ai['length'] = 1
                    ai['dead'] = False
                    del ai_death_times[i]
        # 控制游戏帧率
        clock.tick(snake_speed if not paused else 5)
try:
    gameLoop()
except Exception as e:
    print(f"游戏运行出错: {e}")