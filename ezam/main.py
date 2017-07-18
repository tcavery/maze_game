from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.graphics import Line, Rectangle, Color
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.properties import ObjectProperty
from maze import Maze, Player, Enemy, Gold, Crystal


class GameWidget(BoxLayout):
    def __init__(self, **kwargs):
        super(GameWidget, self).__init__(**kwargs)
        self.load_welcome_screen()

    def new_game(self, *args):
        engine = EngineWidget()
        engine.bind(on_game_over=self.load_game_over_screen)
        engine.bind(on_win=self.load_win_screen)
        self.clear_widgets()
        self.add_widget(engine)

    def load_game_over_screen(self, engine, *args):
        self.clear_widgets()
        game_over_widget = GameOverWidget()
        game_over_widget.new_game_btn.bind(on_release=self.new_game)
        self.add_widget(game_over_widget)

    def load_welcome_screen(self, *args):
        self.clear_widgets()
        welcome_widget = WelcomeWidget()
        welcome_widget.new_game_btn.bind(on_release=self.new_game)
        self.add_widget(welcome_widget)

    def load_win_screen(self, engine, *args):
        self.clear_widgets()
        win_widget = WinWidget()
        win_widget.new_game_btn.bind(on_release=self.new_game)
        self.add_widget(win_widget)

class GameOverWidget(Widget):
    new_game_btn = ObjectProperty(None)

class WelcomeWidget(Widget):
    new_game_btn = ObjectProperty(None)

class WinWidget(Widget):
    new_game_btn = ObjectProperty(None)

class EngineWidget(Widget):
    def __init__(self, **kwargs):
        super(EngineWidget, self).__init__(**kwargs)
        self.register_event_type('on_game_over')
        self.register_event_type('on_win')
        self.cell_width = 20
        self.num_enemies = 5
        self.num_gold = 5
        self.num_crystals = 5

        self.maze = Maze(25, 25)
        self.maze.generate()

        with self.canvas:
            for segment in self.maze.get_wall_segments():
                coords = tuple((val + 0.5) * self.cell_width
                    for val in segment)
                Line(points = coords)

        empty_cells = self.maze.get_empty_cells()

        x,y = empty_cells.pop()
        player = Player(x, y, self.maze)
        self.player_widget = PlayerWidget(player)
        self.add_widget(self.player_widget)

        self.non_player_object_widgets =[]

        for i in range(0, self.num_enemies):
            x,y = empty_cells.pop()
            enemy_widget = EnemyWidget(Enemy(x, y, self.maze))
            self.non_player_object_widgets.append(enemy_widget)
            self.add_widget(enemy_widget)

        for i in range(0, self.num_gold):
            x,y = empty_cells.pop()
            gold_widget = GoldWidget(Gold(x, y, self.maze))
            self.non_player_object_widgets.append(gold_widget)
            self.add_widget(gold_widget)

        for i in range(0, self.num_crystals):
            x,y = empty_cells.pop()
            crystal_widget = CrystalWidget(Crystal(x, y, self.maze))
            self.non_player_object_widgets.append(crystal_widget)
            self.add_widget(crystal_widget)

        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

        self.update_event = Clock.schedule_interval(self.update, 0.01)

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] in ['up', 'down', 'left', 'right']:
            self.player_widget.move(keycode[1])

    def remove_game_object(self, game_object_widget):
        self.non_player_object_widgets.remove(game_object_widget)
        self.remove_widget(game_object_widget)

    def check_collisions(self):
        for widget in self.non_player_object_widgets:
            if widget.collide_widget(self.player_widget):
                widget.game_object.collide(self.player_widget.game_object)

    def update(self, *args):
        self.check_collisions()
        self.player_widget.check_state(self)
        for widget in self.non_player_object_widgets:
            widget.check_state(self)


    def on_game_over(self, *args):
        print("you lose")
        self.update_event.cancel()

    def on_win(self, *args):
        print("you win")
        self.update_event.cancel()


class PlayerWidget(Widget):
    def __init__(self, player, **kwargs):
        super(PlayerWidget, self).__init__(**kwargs)
        self.game_object = player
        self.pos = (20*self.game_object.x+10, 20*self.game_object.y+10)
        self.has_crystal = False
        


    def animate(self):
        animation = Animation(x = 20 * self.game_object.x + 10,
                              y = 20 * self.game_object.y + 10,
                              d = 0.05)
        animation.start(self)

    def move(self, direction):
        self.game_object.move(direction)
        self.animate()

    def check_state(self, engine):
        if self.game_object.marked_for_removal:
            engine.dispatch('on_game_over')
        if self.game_object.gold >= engine.num_gold:
            engine.dispatch('on_win')
        if self.game_object.has_crystal != self.has_crystal:
            self.has_crystal = self.game_object.has_crystal
            color = (1, 0, 1) if self.has_crystal else (0, 1, 0)
            self.canvas.get_group("color")[0].rgb = color
            



class EnemyWidget(Widget):
    def __init__(self, enemy, **kwargs):
        super(EnemyWidget, self).__init__(**kwargs)
        self.game_object = enemy
        self.pos = (20*self.game_object.x+10, 20*self.game_object.y+10)
        self.move_event = Clock.schedule_interval(self.move, 0.3)

    def animate(self):
        animation = Animation(x = 20 * self.game_object.x + 10,
                              y = 20 * self.game_object.y + 10,
                              d = 0.3)
        animation.start(self)

    def move(self, dt):
        self.game_object.move()
        self.animate()

    def check_state(self, engine):
        if self.game_object.marked_for_removal:
            self.move_event.cancel()
            engine.remove_game_object(self)

class GoldWidget(Widget):
    def __init__(self, gold, **kwargs):
        super(GoldWidget, self).__init__(**kwargs)
        self.game_object = gold
        self.pos = (20*self.game_object.x+10, 20*self.game_object.y+10)

    def check_state(self, engine):
        if self.game_object.marked_for_removal:
            engine.remove_game_object(self)

class CrystalWidget(Widget):
    def __init__(self, crystal, **kwargs):
        super(CrystalWidget, self).__init__(**kwargs)
        self.game_object = crystal
        self.pos = (20*self.game_object.x+10, 20*self.game_object.y+10)

    def check_state(self, engine):
        if self.game_object.marked_for_removal:
            engine.remove_game_object(self)



class EzamApp(App):
    def build(self):
        return GameWidget()


if __name__ == '__main__':
    EzamApp().run()