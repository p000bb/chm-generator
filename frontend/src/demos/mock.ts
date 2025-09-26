// 模拟数据 - 仅在开发环境使用
const mockData = {
  inputFolder: "D:\\gen_chm\\projects\\NZ3601\\N32G451xx_V3.3.0\\docs",
  outputFolder: "D:\\code\\electron-chm\\output",
  chipConfig: {
    chipName: "N32G451xx",
    chipVersion: "3.3.0",
    Cn_WebUrl:
      "https://www.nationstech.com/product/general/n32g/n32g45x/n32g451",
    En_WebUrl: "https://nsing.com.sg/product/General/cortexm4/N32G451",
    Zip_Url: "https://www.nationstech.com/uploads/zip/175644003738559.zip",
  },
};

// 根据环境变量判断是否使用模拟数据
const isDev = import.meta.env.DEV;

export const mock = isDev
  ? mockData
  : {
      inputFolder: "",
      outputFolder: "",
      chipConfig: {
        chipName: "",
        chipVersion: "",
        Cn_WebUrl: "",
        En_WebUrl: "",
        Zip_Url: "",
      },
    };
