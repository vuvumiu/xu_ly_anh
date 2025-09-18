# fruit_configs.py - Cấu hình chi tiết cho nhiều loại sản phẩm nông nghiệp
import json


class FruitConfigManager:
    """
    Quản lý cấu hình cho nhiều loại sản phẩm

    Chức năng: Tạo và quản lý cấu hình tối ưu cho từng loại quả
    """

    def __init__(self):
        self.configs = self.create_all_configs()

    def create_all_configs(self):
        """
        Tạo cấu hình cho tất cả các loại sản phẩm

        Return: Dictionary chứa cấu hình cho từng loại quả
        """
        return {
            "tomato": self.create_tomato_config(),
            "apple": self.create_apple_config(),
            "banana": self.create_banana_config(),
            "guava": self.create_guava_config(),
            "orange": self.create_orange_config(),
            "mango": self.create_mango_config(),
            "lemon": self.create_lemon_config(),
            "papaya": self.create_papaya_config(),
            "dragon_fruit": self.create_dragon_fruit_config(),
            "passion_fruit": self.create_passion_fruit_config(),
            "rambutan": self.create_rambutan_config(),
            "longan": self.create_longan_config()
        }

    def create_tomato_config(self):
        """Cấu hình cho cà chua"""
        return {
            "name": "Cà chua",
            "name_en": "Tomato",
            "product": "tomato",
            "description": "Cà chua tròn, phân loại theo độ chín và kích thước",

            "size_thresholds_mm": {
                "S": [0, 55],  # Cà chua cherry, bi
                "M": [55, 65],  # Cà chua vừa
                "L": [65, 75],  # Cà chua lớn
                "XL": [75, 999]  # Cà chua siêu to
            },

            "hsv_ranges": {
                "red": [  # Cà chua chín đỏ
                    {"H": [0, 10], "S": [80, 255], "V": [70, 255]},
                    {"H": [160, 180], "S": [80, 255], "V": [70, 255]}
                ],
                "green": [  # Cà chua xanh non
                    {"H": [35, 85], "S": [60, 255], "V": [60, 255]}
                ],
                "yellow": [  # Cà chua vàng, chuyển màu
                    {"H": [15, 35], "S": [50, 255], "V": [50, 255]}
                ]
            },

            "lab_thresholds": {
                "a_star_ripe_min": 25,  # Kênh a* cho màu đỏ chín
                "a_star_green_max": 10,  # Kênh a* cho màu xanh
                "l_star_min": 50  # Độ sáng tối thiểu
            },

            "ripeness_logic": {
                "green_if": {
                    "ratio_red_max": 0.15,
                    "a_star_max": 10,
                    "ratio_green_min": 0.60
                },
                "ripe_if": {
                    "ratio_red_min": 0.35,
                    "a_star_min": 20,
                    "ratio_green_max": 0.20
                }
            },

            "defect": {
                "dark_delta_T": 25,  # Ngưỡng phát hiện đốm tối
                "area_ratio_tau": 0.06,  # Tỷ lệ diện tích khuyết tật tối đa
                "contrast_threshold": 30  # Ngưỡng tương phản
            },

            "morphology": {
                "open_kernel": 3,
                "close_kernel": 5,
                "min_area": 200,
                "max_area": 50000
            },

            "watershed": {
                "distance_threshold_rel": 0.5,
                "min_distance": 10
            },

            "shape_constraints": {
                "min_circularity": 0.7,  # Cà chua khá tròn
                "max_aspect_ratio": 1.3  # Không quá dài
            }
        }

    def create_apple_config(self):
        """Cấu hình cho táo"""
        return {
            "name": "Táo",
            "name_en": "Apple",
            "product": "apple",
            "description": "Táo tròn, nhiều màu sắc",

            "size_thresholds_mm": {
                "S": [0, 60],
                "M": [60, 70],
                "L": [70, 85],
                "XL": [85, 999]
            },

            "hsv_ranges": {
                "red": [  # Táo đỏ
                    {"H": [0, 15], "S": [100, 255], "V": [80, 255]},
                    {"H": [165, 180], "S": [100, 255], "V": [80, 255]}
                ],
                "green": [  # Táo xanh
                    {"H": [40, 80], "S": [50, 255], "V": [60, 255]}
                ],
                "yellow": [  # Táo vàng
                    {"H": [20, 40], "S": [60, 255], "V": [70, 255]}
                ]
            },

            "lab_thresholds": {
                "a_star_ripe_min": 20,
                "a_star_green_max": 15,
                "l_star_min": 60
            },

            "ripeness_logic": {
                "green_if": {
                    "ratio_red_max": 0.20,
                    "a_star_max": 15,
                    "l_star_max": 120
                },
                "ripe_if": {
                    "ratio_red_min": 0.40,
                    "a_star_min": 18,
                    "l_star_min": 80
                }
            },

            "defect": {
                "dark_delta_T": 30,
                "area_ratio_tau": 0.08,
                "contrast_threshold": 35
            },

            "morphology": {
                "open_kernel": 4,
                "close_kernel": 6,
                "min_area": 300,
                "max_area": 60000
            },

            "watershed": {
                "distance_threshold_rel": 0.45,
                "min_distance": 15
            },

            "shape_constraints": {
                "min_circularity": 0.75,
                "max_aspect_ratio": 1.2
            }
        }

    def create_banana_config(self):
        """Cấu hình cho chuối"""
        return {
            "name": "Chuối",
            "name_en": "Banana",
            "product": "banana",
            "description": "Chuối dài, cong, màu vàng khi chín",

            "size_thresholds_mm": {
                "S": [0, 120],  # Chuối nhỏ
                "M": [120, 150],  # Chuối vừa
                "L": [150, 180],  # Chuối lớn
                "XL": [180, 999]  # Chuối siêu to
            },

            "hsv_ranges": {
                "yellow": [  # Chuối chín vàng
                    {"H": [15, 35], "S": [80, 255], "V": [80, 255]}
                ],
                "green": [  # Chuối xanh
                    {"H": [40, 80], "S": [60, 255], "V": [60, 255]}
                ],
                "brown": [  # Chuối quá chín, nâu
                    {"H": [5, 25], "S": [50, 200], "V": [30, 100]}
                ]
            },

            "lab_thresholds": {
                "b_star_yellow_min": 20,  # Kênh b* cho màu vàng
                "a_star_green_max": 10,
                "l_star_min": 40
            },

            "ripeness_logic": {
                "green_if": {
                    "ratio_yellow_max": 0.30,
                    "b_star_max": 15,
                    "ratio_green_min": 0.50
                },
                "ripe_if": {
                    "ratio_yellow_min": 0.70,
                    "b_star_min": 25,
                    "ratio_brown_max": 0.10
                }
            },

            "defect": {
                "dark_delta_T": 20,
                "area_ratio_tau": 0.05,  # Chuối ít khuyết tật hơn
                "contrast_threshold": 25
            },

            "morphology": {
                "open_kernel": 3,
                "close_kernel": 4,
                "min_area": 400,
                "max_area": 80000
            },

            "watershed": {
                "distance_threshold_rel": 0.3,  # Thấp hơn do hình dài
                "min_distance": 20
            },

            "shape_constraints": {
                "min_aspect_ratio": 2.5,  # Chuối phải dài
                "max_aspect_ratio": 6.0,
                "min_circularity": 0.3  # Không tròn
            }
        }

    def create_guava_config(self):
        """Cấu hình cho ổi"""
        return {
            "name": "Ổi",
            "name_en": "Guava",
            "product": "guava",
            "description": "Ổi tròn to, màu xanh chuyển trắng khi chín",

            "size_thresholds_mm": {
                "S": [0, 50],
                "M": [50, 70],
                "L": [70, 90],
                "XL": [90, 999]
            },

            "hsv_ranges": {
                "green": [  # Ổi xanh
                    {"H": [40, 90], "S": [30, 255], "V": [60, 255]}
                ],
                "white": [  # Ổi chín trắng
                    {"H": [0, 180], "S": [0, 50], "V": [150, 255]}
                ],
                "yellow": [  # Ổi vàng nhạt
                    {"H": [20, 40], "S": [40, 255], "V": [100, 255]}
                ]
            },

            "lab_thresholds": {
                "a_star_ripe_min": 5,  # Ổi chín ít đỏ
                "l_star_min": 120,  # Ổi chín sáng màu
                "l_star_ripe_min": 160  # Ổi chín rất sáng
            },

            "ripeness_logic": {
                "green_if": {
                    "ratio_white_max": 0.20,
                    "l_star_max": 140,
                    "ratio_green_min": 0.60
                },
                "ripe_if": {
                    "ratio_white_min": 0.50,
                    "l_star_min": 160,
                    "ratio_green_max": 0.30
                }
            },

            "defect": {
                "dark_delta_T": 35,
                "area_ratio_tau": 0.04,  # Ổi ít bị đốm
                "contrast_threshold": 40
            },

            "morphology": {
                "open_kernel": 4,
                "close_kernel": 6,
                "min_area": 250,
                "max_area": 70000
            },

            "watershed": {
                "distance_threshold_rel": 0.55,
                "min_distance": 12
            },

            "shape_constraints": {
                "min_circularity": 0.65,
                "max_aspect_ratio": 1.4
            }
        }

    def create_orange_config(self):
        """Cấu hình cho cam"""
        return {
            "name": "Cam",
            "name_en": "Orange",
            "product": "orange",
            "description": "Cam tròn, màu cam đặc trưng",

            "size_thresholds_mm": {
                "S": [0, 65],
                "M": [65, 75],
                "L": [75, 90],
                "XL": [90, 999]
            },

            "hsv_ranges": {
                "orange": [  # Cam chín
                    {"H": [5, 25], "S": [100, 255], "V": [100, 255]}
                ],
                "yellow": [  # Cam vàng
                    {"H": [25, 40], "S": [80, 255], "V": [120, 255]}
                ],
                "green": [  # Cam xanh
                    {"H": [40, 80], "S": [60, 255], "V": [80, 255]}
                ]
            },

            "lab_thresholds": {
                "a_star_ripe_min": 15,
                "b_star_orange_min": 30,  # Kênh b* cho cam
                "l_star_min": 70
            },

            "ripeness_logic": {
                "green_if": {
                    "ratio_orange_max": 0.25,
                    "b_star_max": 20,
                    "ratio_green_min": 0.50
                },
                "ripe_if": {
                    "ratio_orange_min": 0.60,
                    "b_star_min": 35,
                    "a_star_min": 15
                }
            },

            "defect": {
                "dark_delta_T": 25,
                "area_ratio_tau": 0.06,
                "contrast_threshold": 30
            },

            "morphology": {
                "open_kernel": 3,
                "close_kernel": 5,
                "min_area": 300,
                "max_area": 55000
            },

            "watershed": {
                "distance_threshold_rel": 0.5,
                "min_distance": 12
            },

            "shape_constraints": {
                "min_circularity": 0.75,
                "max_aspect_ratio": 1.2
            }
        }

    def create_mango_config(self):
        """Cấu hình cho xoài"""
        return {
            "name": "Xoài",
            "name_en": "Mango",
            "product": "mango",
            "description": "Xoài hình oval, màu vàng khi chín",

            "size_thresholds_mm": {
                "S": [0, 80],
                "M": [80, 120],
                "L": [120, 160],
                "XL": [160, 999]
            },

            "hsv_ranges": {
                "yellow": [  # Xoài chín vàng
                    {"H": [15, 35], "S": [80, 255], "V": [100, 255]}
                ],
                "green": [  # Xoài xanh
                    {"H": [40, 80], "S": [60, 255], "V": [70, 255]}
                ],
                "red": [  # Xoài có má đỏ
                    {"H": [0, 15], "S": [80, 255], "V": [80, 255]}
                ]
            },

            "lab_thresholds": {
                "a_star_ripe_min": 10,
                "b_star_yellow_min": 25,
                "l_star_min": 60
            },

            "ripeness_logic": {
                "green_if": {
                    "ratio_yellow_max": 0.30,
                    "b_star_max": 20,
                    "ratio_green_min": 0.60
                },
                "ripe_if": {
                    "ratio_yellow_min": 0.60,
                    "b_star_min": 30,
                    "l_star_min": 80
                }
            },

            "defect": {
                "dark_delta_T": 28,
                "area_ratio_tau": 0.07,
                "contrast_threshold": 32
            },

            "morphology": {
                "open_kernel": 4,
                "close_kernel": 5,
                "min_area": 350,
                "max_area": 90000
            },

            "watershed": {
                "distance_threshold_rel": 0.45,
                "min_distance": 18
            },

            "shape_constraints": {
                "min_circularity": 0.6,  # Xoài hơi oval
                "max_aspect_ratio": 2.0
            }
        }

    def create_lemon_config(self):
        """Cấu hình cho chanh"""
        return {
            "name": "Chanh",
            "name_en": "Lemon",
            "product": "lemon",
            "description": "Chanh tròn hoặc oval, màu vàng xanh",

            "size_thresholds_mm": {
                "S": [0, 40],
                "M": [40, 50],
                "L": [50, 65],
                "XL": [65, 999]
            },

            "hsv_ranges": {
                "yellow": [  # Chanh vàng
                    {"H": [20, 40], "S": [80, 255], "V": [80, 255]}
                ],
                "green": [  # Chanh xanh
                    {"H": [40, 80], "S": [80, 255], "V": [70, 255]}
                ],
                "lime": [  # Chanh ta
                    {"H": [60, 90], "S": [100, 255], "V": [60, 200]}
                ]
            },

            "lab_thresholds": {
                "b_star_yellow_min": 15,
                "a_star_green_max": 5,
                "l_star_min": 50
            },

            "ripeness_logic": {
                "green_if": {
                    "ratio_yellow_max": 0.25,
                    "b_star_max": 10,
                    "ratio_green_min": 0.70
                },
                "ripe_if": {
                    "ratio_yellow_min": 0.70,
                    "b_star_min": 20,
                    "l_star_min": 90
                }
            },

            "defect": {
                "dark_delta_T": 30,
                "area_ratio_tau": 0.05,
                "contrast_threshold": 35
            },

            "morphology": {
                "open_kernel": 2,
                "close_kernel": 4,
                "min_area": 150,
                "max_area": 25000
            },

            "watershed": {
                "distance_threshold_rel": 0.6,
                "min_distance": 8
            },

            "shape_constraints": {
                "min_circularity": 0.65,
                "max_aspect_ratio": 1.5
            }
        }

    def create_papaya_config(self):
        """Cấu hình cho đu đủ"""
        return {
            "name": "Đu đủ",
            "name_en": "Papaya",
            "product": "papaya",
            "description": "Đu đủ oval lớn, xanh chuyển vàng cam",

            "size_thresholds_mm": {
                "S": [0, 150],
                "M": [150, 200],
                "L": [200, 300],
                "XL": [300, 999]
            },

            "hsv_ranges": {
                "orange": [  # Đu đủ chín
                    {"H": [5, 25], "S": [70, 255], "V": [80, 255]}
                ],
                "yellow": [  # Đu đủ vàng
                    {"H": [25, 40], "S": [60, 255], "V": [100, 255]}
                ],
                "green": [  # Đu đủ xanh
                    {"H": [40, 85], "S": [50, 255], "V": [60, 255]}
                ]
            },

            "lab_thresholds": {
                "a_star_ripe_min": 20,
                "b_star_orange_min": 35,
                "l_star_min": 70
            },

            "ripeness_logic": {
                "green_if": {
                    "ratio_orange_max": 0.20,
                    "b_star_max": 25,
                    "ratio_green_min": 0.70
                },
                "ripe_if": {
                    "ratio_orange_min": 0.50,
                    "b_star_min": 40,
                    "a_star_min": 25
                }
            },

            "defect": {
                "dark_delta_T": 35,
                "area_ratio_tau": 0.08,
                "contrast_threshold": 40
            },

            "morphology": {
                "open_kernel": 5,
                "close_kernel": 7,
                "min_area": 800,
                "max_area": 150000
            },

            "watershed": {
                "distance_threshold_rel": 0.4,
                "min_distance": 25
            },

            "shape_constraints": {
                "min_circularity": 0.5,
                "max_aspect_ratio": 2.5
            }
        }

    def create_dragon_fruit_config(self):
        """Cấu hình cho thanh long"""
        return {
            "name": "Thanh long",
            "name_en": "Dragon fruit",
            "product": "dragon_fruit",
            "description": "Thanh long oval, vỏ hồng có vẩy xanh",

            "size_thresholds_mm": {
                "S": [0, 80],
                "M": [80, 120],
                "L": [120, 160],
                "XL": [160, 999]
            },

            "hsv_ranges": {
                "pink": [  # Vỏ hồng
                    {"H": [140, 170], "S": [50, 255], "V": [80, 255]},
                    {"H": [0, 10], "S": [50, 255], "V": [80, 255]}
                ],
                "green": [  # Vẩy xanh
                    {"H": [40, 80], "S": [80, 255], "V": [60, 200]}
                ],
                "white": [  # Thanh long trắng
                    {"H": [0, 180], "S": [0, 30], "V": [150, 255]}
                ]
            },

            "lab_thresholds": {
                "a_star_pink_min": 15,
                "b_star_min": 0,
                "l_star_min": 60
            },

            "ripeness_logic": {
                "green_if": {
                    "ratio_pink_max": 0.40,
                    "ratio_green_min": 0.30,
                    "l_star_max": 120
                },
                "ripe_if": {
                    "ratio_pink_min": 0.70,
                    "a_star_min": 18,
                    "l_star_min": 90
                }
            },

            "defect": {
                "dark_delta_T": 40,
                "area_ratio_tau": 0.06,
                "contrast_threshold": 45
            },

            "morphology": {
                "open_kernel": 4,
                "close_kernel": 6,
                "min_area": 400,
                "max_area": 80000
            },

            "watershed": {
                "distance_threshold_rel": 0.45,
                "min_distance": 15
            },

            "shape_constraints": {
                "min_circularity": 0.6,
                "max_aspect_ratio": 1.8
            }
        }

    def create_passion_fruit_config(self):
        """Cấu hình cho chanh dây"""
        return {
            "name": "Chanh dây",
            "name_en": "Passion fruit",
            "product": "passion_fruit",
            "description": "Chanh dây tròn, vỏ tím hoặc vàng",

            "size_thresholds_mm": {
                "S": [0, 45],
                "M": [45, 60],
                "L": [60, 75],
                "XL": [75, 999]
            },

            "hsv_ranges": {
                "purple": [  # Chanh dây tím
                    {"H": [120, 150], "S": [80, 255], "V": [40, 200]}
                ],
                "yellow": [  # Chanh dây vàng
                    {"H": [20, 40], "S": [80, 255], "V": [80, 255]}
                ],
                "brown": [  # Chín quá, nhăn
                    {"H": [10, 30], "S": [50, 200], "V": [30, 120]}
                ]
            },

            "lab_thresholds": {
                "a_star_purple_min": 20,
                "b_star_yellow_min": 20,
                "l_star_min": 40
            },

            "ripeness_logic": {
                "green_if": {
                    "l_star_min": 100,
                    "texture_smooth": True
                },
                "ripe_if": {
                    "ratio_purple_min": 0.60,
                    "texture_wrinkled": True,
                    "l_star_max": 80
                }
            },

            "defect": {
                "dark_delta_T": 20,
                "area_ratio_tau": 0.04,
                "contrast_threshold": 25
            },

            "morphology": {
                "open_kernel": 3,
                "close_kernel": 4,
                "min_area": 200,
                "max_area": 30000
            },

            "watershed": {
                "distance_threshold_rel": 0.6,
                "min_distance": 10
            },

            "shape_constraints": {
                "min_circularity": 0.75,
                "max_aspect_ratio": 1.2
            }
        }

    def create_rambutan_config(self):
        """Cấu hình cho chôm chôm"""
        return {
            "name": "Chôm chôm",
            "name_en": "Rambutan",
            "product": "rambutan",
            "description": "Chôm chôm tròn có gai, đỏ khi chín",

            "size_thresholds_mm": {
                "S": [0, 35],
                "M": [35, 45],
                "L": [45, 55],
                "XL": [55, 999]
            },

            "hsv_ranges": {
                "red": [  # Chôm chôm chín đỏ
                    {"H": [0, 15], "S": [120, 255], "V": [80, 255]},
                    {"H": [160, 180], "S": [120, 255], "V": [80, 255]}
                ],
                "yellow": [  # Chôm chôm vàng
                    {"H": [15, 35], "S": [100, 255], "V": [100, 255]}
                ],
                "green": [  # Chôm chôm xanh
                    {"H": [40, 80], "S": [80, 255], "V": [70, 200]}
                ]
            },

            "lab_thresholds": {
                "a_star_ripe_min": 30,  # Đỏ rõ rệt
                "l_star_min": 50
            },

            "ripeness_logic": {
                "green_if": {
                    "ratio_red_max": 0.20,
                    "ratio_green_min": 0.60,
                    "a_star_max": 15
                },
                "ripe_if": {
                    "ratio_red_min": 0.70,
                    "a_star_min": 35,
                    "l_star_min": 70
                }
            },

            "defect": {
                "dark_delta_T": 25,
                "area_ratio_tau": 0.05,
                "contrast_threshold": 30
            },

            "morphology": {
                "open_kernel": 2,
                "close_kernel": 3,
                "min_area": 150,
                "max_area": 15000
            },

            "watershed": {
                "distance_threshold_rel": 0.5,
                "min_distance": 8
            },

            "shape_constraints": {
                "min_circularity": 0.7,
                "max_aspect_ratio": 1.3
            },

            "texture_analysis": {
                "detect_spikes": True,
                "spike_threshold": 0.3
            }
        }

    def create_longan_config(self):
        """Cấu hình cho nhãn"""
        return {
            "name": "Nhãn",
            "name_en": "Longan",
            "product": "longan",
            "description": "Nhãn tròn nhỏ, vỏ nâu vàng",

            "size_thresholds_mm": {
                "S": [0, 20],
                "M": [20, 25],
                "L": [25, 30],
                "XL": [30, 999]
            },

            "hsv_ranges": {
                "brown": [  # Nhãn chín nâu
                    {"H": [10, 25], "S": [80, 255], "V": [60, 200]}
                ],
                "yellow": [  # Nhãn vàng
                    {"H": [25, 40], "S": [60, 255], "V": [80, 255]}
                ],
                "green": [  # Nhãn xanh non
                    {"H": [40, 80], "S": [60, 255], "V": [70, 200]}
                ]
            },

            "lab_thresholds": {
                "a_star_brown_min": 10,
                "b_star_brown_min": 15,
                "l_star_min": 40
            },

            "ripeness_logic": {
                "green_if": {
                    "ratio_brown_max": 0.20,
                    "ratio_green_min": 0.60,
                    "l_star_max": 100
                },
                "ripe_if": {
                    "ratio_brown_min": 0.60,
                    "b_star_min": 20,
                    "l_star_min": 60
                }
            },

            "defect": {
                "dark_delta_T": 20,
                "area_ratio_tau": 0.03,
                "contrast_threshold": 25
            },

            "morphology": {
                "open_kernel": 1,
                "close_kernel": 2,
                "min_area": 80,
                "max_area": 8000
            },

            "watershed": {
                "distance_threshold_rel": 0.6,
                "min_distance": 5
            },

            "shape_constraints": {
                "min_circularity": 0.8,
                "max_aspect_ratio": 1.2
            }
        }

    def get_config(self, fruit_type):
        """
        Lấy cấu hình cho loại quả cụ thể

        Args:
            fruit_type: Tên loại quả

        Returns:
            Dictionary cấu hình hoặc None nếu không tìm thấy
        """
        return self.configs.get(fruit_type)

    def get_all_fruit_names(self):
        """Lấy danh sách tên tất cả các loại quả"""
        return [(key, config['name']) for key, config in self.configs.items()]

    def save_config_to_file(self, fruit_type, filename):
        """
        Lưu cấu hình ra file JSON

        Args:
            fruit_type: Loại quả
            filename: Tên file để lưu
        """
        config = self.get_config(fruit_type)
        if config:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        return False

    def load_custom_config(self, filename):
        """
        Tải cấu hình tùy chỉnh từ file

        Args:
            filename: Đường dẫn file cấu hình

        Returns:
            Dictionary cấu hình
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Lỗi tải cấu hình: {e}")
            return None

    def create_config_template(self, fruit_name):
        """
        Tạo template cấu hình cho loại quả mới

        Args:
            fruit_name: Tên loại quả mới

        Returns:
            Dictionary template cấu hình
        """
        template = {
            "name": fruit_name,
            "name_en": fruit_name.lower().replace(" ", "_"),
            "product": fruit_name.lower().replace(" ", "_"),
            "description": f"Cấu hình cho {fruit_name}",

            "size_thresholds_mm": {
                "S": [0, 50],
                "M": [50, 70],
                "L": [70, 90],
                "XL": [90, 999]
            },

            "hsv_ranges": {
                "primary_color": [
                    {"H": [0, 30], "S": [80, 255], "V": [80, 255]}
                ],
                "secondary_color": [
                    {"H": [40, 80], "S": [60, 255], "V": [60, 255]}
                ]
            },

            "lab_thresholds": {
                "a_star_ripe_min": 15,
                "l_star_min": 50
            },

            "ripeness_logic": {
                "green_if": {
                    "ratio_primary_max": 0.30,
                    "a_star_max": 10
                },
                "ripe_if": {
                    "ratio_primary_min": 0.60,
                    "a_star_min": 20
                }
            },

            "defect": {
                "dark_delta_T": 25,
                "area_ratio_tau": 0.06,
                "contrast_threshold": 30
            },

            "morphology": {
                "open_kernel": 3,
                "close_kernel": 5,
                "min_area": 200,
                "max_area": 50000
            },

            "watershed": {
                "distance_threshold_rel": 0.5,
                "min_distance": 10
            },

            "shape_constraints": {
                "min_circularity": 0.6,
                "max_aspect_ratio": 2.0
            }
        }

        return template

    def validate_config(self, config):
        """
        Kiểm tra tính hợp lệ của cấu hình

        Args:
            config: Dictionary cấu hình cần kiểm tra

        Returns:
            Tuple (is_valid, error_messages)
        """
        errors = []
        required_keys = [
            'name', 'product', 'size_thresholds_mm',
            'hsv_ranges', 'ripeness_logic', 'defect',
            'morphology', 'watershed'
        ]

        # Kiểm tra các key bắt buộc
        for key in required_keys:
            if key not in config:
                errors.append(f"Thiếu key bắt buộc: {key}")

        # Kiểm tra size thresholds
        if 'size_thresholds_mm' in config:
            sizes = config['size_thresholds_mm']
            for size_name, (min_val, max_val) in sizes.items():
                if min_val >= max_val:
                    errors.append(f"Kích thước {size_name}: min >= max")

        # Kiểm tra HSV ranges
        if 'hsv_ranges' in config:
            for color, ranges in config['hsv_ranges'].items():
                for i, range_dict in enumerate(ranges):
                    for channel in ['H', 'S', 'V']:
                        if channel not in range_dict:
                            errors.append(f"HSV range {color}[{i}] thiếu kênh {channel}")
                        elif len(range_dict[channel]) != 2:
                            errors.append(f"HSV range {color}[{i}] kênh {channel} phải có 2 giá trị")

        return len(errors) == 0, errors


# Ví dụ sử dụng
if __name__ == "__main__":
    # Khởi tạo manager
    config_manager = FruitConfigManager()

    # In danh sách các loại quả
    print("Các loại sản phẩm có sẵn:")
    for key, name in config_manager.get_all_fruit_names():
        print(f"- {key}: {name}")

    # Lưu cấu hình cà chua
    config_manager.save_config_to_file('tomato', 'tomato_config.json')
    print("\nĐã lưu cấu hình cà chua vào tomato_config.json")

    # Tạo template cho loại quả mới
    new_fruit_template = config_manager.create_config_template("Dưa hấu")
    with open('watermelon_template.json', 'w', encoding='utf-8') as f:
        json.dump(new_fruit_template, f, indent=2, ensure_ascii=False)
    print("Đã tạo template cho dưa hấu: watermelon_template.json")

    # Kiểm tra tính hợp lệ
    tomato_config = config_manager.get_config('tomato')
    is_valid, errors = config_manager.validate_config(tomato_config)
    print(f"\nCấu hình cà chua hợp lệ: {is_valid}")
    if errors:
        for error in errors:
            print(f"- {error}")