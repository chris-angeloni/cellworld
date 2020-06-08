#include <view.h>
#include <iostream>
#include <fstream>

using namespace ge211;
using namespace std;
namespace cell_world {

    View::View(const Cell_group &cg, Dimensions scene_dimensions) :
            _cell_group(cg),
            _scene_dimensions(scene_dimensions) {
        double sx, sy, lx, ly;
        lx = sx = _cell_group[0].location.x;
        ly = sy = _cell_group[0].location.y;
        for (unsigned int i = 0; i < _cell_group.size(); i++) {
            double x = _cell_group[i].location.x;
            double y = _cell_group[i].location.y;
            if (lx < x) lx = x;
            if (ly < y) ly = y;
            if (sx > x) sx = x;
            if (sy > y) sy = y;
        }
        double rx = (_scene_dimensions.width - 100) / (lx - sx);
        double ry = (_scene_dimensions.height - 100) / (ly - sy);
        _ratio = rx < ry ? rx : ry;
        _cell_size = (int) _ratio / 2 - 1;
        _circle_sprites.emplace_back(_cell_size, ge211::Color{0, 0, 0}); //0
        _circle_sprites.emplace_back(_cell_size, ge211::Color{255, 255, 255}); //1
        _circle_sprites.emplace_back(_cell_size, ge211::Color{255, 0, 0}); //2
        _circle_sprites.emplace_back(_cell_size, ge211::Color{0, 255, 0}); //3
        _circle_sprites.emplace_back(_cell_size, ge211::Color{0, 0, 255}); //4
        _circle_sprites.emplace_back(_cell_size, ge211::Color{255, 255, 0}); //5
        _circle_sprites.emplace_back(_cell_size, ge211::Color{0, 255, 255}); //6
        _circle_sprites.emplace_back(_cell_size, ge211::Color{255, 0, 255}); //7
        _circle_sprites.emplace_back(_cell_size, ge211::Color{192, 192, 192}); //8
        _circle_sprites.emplace_back(_cell_size, ge211::Color{128, 128, 128}); //9
        _circle_sprites.emplace_back(_cell_size, ge211::Color{128, 0, 0}); //10
        _circle_sprites.emplace_back(_cell_size, ge211::Color{128, 128, 0}); //11
        _circle_sprites.emplace_back(_cell_size, ge211::Color{0, 128, 0}); //12
        _circle_sprites.emplace_back(_cell_size, ge211::Color{128, 0, 128}); //13
        _circle_sprites.emplace_back(_cell_size, ge211::Color{0, 128, 128}); //14
        _circle_sprites.emplace_back(_cell_size, ge211::Color{0, 0, 128}); //15
        for (uint i = 0; i < 256; i++) {
            _circle_value_sprites.emplace_back(_cell_size, ge211::Color{255, (uint8_t) (255 - i), (uint8_t) (255 - i)});
        }
        Dimensions d{_cell_size * 2, _cell_size * 2};
        _square_sprites.emplace_back(d, ge211::Color{0, 0, 0}); //0
        _square_sprites.emplace_back(d, ge211::Color{255, 255, 255}); //1
        _square_sprites.emplace_back(d, ge211::Color{255, 0, 0}); //2
        _square_sprites.emplace_back(d, ge211::Color{0, 255, 0}); //3
        _square_sprites.emplace_back(d, ge211::Color{0, 0, 255}); //4
        _square_sprites.emplace_back(d, ge211::Color{255, 255, 0}); //5
        _square_sprites.emplace_back(d, ge211::Color{0, 255, 255}); //6
        _square_sprites.emplace_back(d, ge211::Color{255, 0, 255}); //7
        _square_sprites.emplace_back(d, ge211::Color{192, 192, 192}); //8
        _square_sprites.emplace_back(d, ge211::Color{128, 128, 128}); //9
        _square_sprites.emplace_back(d, ge211::Color{128, 0, 0}); //10
        _square_sprites.emplace_back(d, ge211::Color{128, 128, 0}); //11
        _square_sprites.emplace_back(d, ge211::Color{0, 128, 0}); //12
        _square_sprites.emplace_back(d, ge211::Color{128, 0, 128}); //13
        _square_sprites.emplace_back(d, ge211::Color{0, 128, 128}); //14
        _square_sprites.emplace_back(d, ge211::Color{0, 0, 128}); //15
        for (uint i = 0; i < 256; i++) {
            _square_value_sprites.emplace_back(d, ge211::Color{255, (uint8_t) (255 - i), (uint8_t) (255 - i)});
        }
        int icon_counter = 1;
        string file_name;
        {
            std::stringstream fmt;
            fmt << "icon-" << icon_counter << ".png";
            file_name = resource_file(fmt.str());
        }
        while (file_exists(file_name)) {
            _icon_sprites.emplace_back(file_name);
            {
                std::stringstream fmt;
                icon_counter++;
                fmt << "icon-" << icon_counter << ".png";
                file_name = resource_file(fmt.str());
            }
        }
        icon_counter = 0;
        {
            std::stringstream fmt;
            fmt << "icons/custom-icon-" << icon_counter << ".png";
            file_name = fmt.str();
        }
        while (file_exists(file_name)) {
            _custom_icon_sprites.emplace_back(file_name);
            {
                std::stringstream fmt;
                icon_counter++;
                fmt << "icons/custom-icon-" << icon_counter << ".png";
                file_name = fmt.str();
            }
        }
    }

    Basic_position<int> View::_screen_location(const Location &location) const {
        return {
                (int) ((double) _scene_dimensions.width / 2 + location.x * _ratio - _ratio / 2),
                (int) ((double) _scene_dimensions.height / 2 + location.y * _ratio - _ratio / 2)
        };
    }

    void View::draw_scene(Sprite_set &sprites, const vector<Agent_data> &agents, const string &text) {
        fps.reconfigure(Text_sprite::Builder(sans) << text);
        sprites.add_sprite(fps, {10, 10});
        _draw_world(sprites);
        for (auto &agent : agents) {
            auto &cell = agent.cell;
            if (cell.cell_type == Circle) {
                sprites.add_sprite(_circle_sprites[agent.color], _screen_location(cell.location), 1);
            } else {
                sprites.add_sprite(_square_sprites[agent.color], _screen_location(cell.location), 1);
            }
            if (agent.icon) {
                sprites.add_sprite(
                        agent.icon < 100 ? _icon_sprites[agent.icon - 1] : _custom_icon_sprites[agent.icon - 100],

                        _screen_location(cell.location), 100,
                        Transform::scale((double) _cell_size / 128.0));
            }
        }
    }

    void View::draw_editor(ge211::Sprite_set &sprites,  int index, std::vector<Cell_group_view> groups,
                           const std::string &text) {
        if (!text.empty()) {
            fps.reconfigure(Text_sprite::Builder(sans) << text);
            sprites.add_sprite(fps, {10, 10});
        }
        _draw_world(sprites);
        for (unsigned int group_index = 0; group_index < groups.size(); group_index++) {
            Cell_group_view &gv = groups[group_index];
            if (gv.show) {
                Cell_group &cells = gv.cells;
                for (unsigned int i = 0; i < cells.size(); i++) {
                    if (cells[i].cell_type == Circle) {
                        sprites.add_sprite(_circle_sprites[gv.color], _screen_location(cells[i].location),
                                           2 + (int) group_index);
                    } else {
                        sprites.add_sprite(_square_sprites[gv.color], _screen_location(cells[i].location),
                                           2 + (int) group_index);
                    }
                }
            }
        }
        if (index >= 0) {
            if (_cell_group[index].cell_type == Circle) {
                if (_cell_group[index].occluded)
                    sprites.add_sprite(_circle_sprites[12], _screen_location(_cell_group[index].location), 255);
                else
                    sprites.add_sprite(_circle_sprites[3], _screen_location(_cell_group[index].location), 255);
            } else {
                if (_cell_group[index].occluded)
                    sprites.add_sprite(_square_sprites[12], _screen_location(_cell_group[index].location), 255);
                else
                    sprites.add_sprite(_square_sprites[3], _screen_location(_cell_group[index].location), 255);
            }
        }
    }

    void View::_draw_world(ge211::Sprite_set &sprites) {
        for (unsigned int i = 0; i < _cell_group.size(); i++) {
            const Cell &cell = _cell_group[i];
            if (cell.cell_type == Circle) {
                if (cell.occluded) {
                    sprites.add_sprite(_circle_sprites[9], _screen_location(cell.location), 0);
                } else {
                    sprites.add_sprite(_circle_value_sprites[cell.value * 255], _screen_location(cell.location), 0);
                }
            } else {
                if (cell.occluded) {
                    sprites.add_sprite(_square_sprites[9], _screen_location(cell.location), 0);
                } else {
                    sprites.add_sprite(_square_value_sprites[cell.value * 255], _screen_location(cell.location), 0);
                }
            }
            if (cell.icon) {
                sprites.add_sprite(
                        cell.icon < 100 ? _icon_sprites[cell.icon - 1] : _custom_icon_sprites[cell.icon - 100],
                        _screen_location(cell.location), 100,
                        Transform::scale((double) _cell_size / 128.0).set_rotation(
                                cell.direction.rotation()));
            }
        }
    }

     int View::get_cell(ge211::Position mouse_position) {
        for (unsigned int i = 0; i < _cell_group.size(); i++) {
            const Cell &cell = _cell_group[i];
            ge211::Position cell_pos = _screen_location(cell.location);
            cell_pos.x += _cell_size;
            cell_pos.y += _cell_size;
            double distance = sqrt(pow(mouse_position.y - cell_pos.y, 2) + pow(mouse_position.x - cell_pos.x, 2));
            if (distance <= _cell_size) {
                return i;
            }
        }
        return Not_found;
    }

    std::string View::resource_file(const std::string &res) {
        string file_name(CELLWORLD_RESOURCES);
        return file_name + "/" + res;
    }

    bool View::file_exists(const std::string &name) {
        ifstream f(name.c_str());
        return f.good();
    }
}