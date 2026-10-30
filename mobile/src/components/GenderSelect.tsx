import {Text, View} from "react-native";
import {Button} from "./UI";
import {styles as s} from "../theme";
export function GenderSelect({value,onChange}:{value:"male"|"female"|null;onChange:(value:"male"|"female"|null)=>void}) {
  return <View style={{gap:8}}><Text style={s.label}>Пол · необязательно</Text><View style={{flexDirection:"row",flexWrap:"wrap",gap:8}}>{([['female','Женщина'],['male','Мужчина'],[null,'Не указан']] as const).map(([gender,label])=><Button key={gender || 'unknown'} secondary={value!==gender} label={label} onPress={()=>onChange(gender)} />)}</View></View>;
}
