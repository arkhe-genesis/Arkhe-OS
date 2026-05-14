
import React from 'react';
import { SafeAreaView, Text, View } from 'react-native';
const App = () => {
  const [phiC, setPhiC] = React.useState(0.997);
  return (
    <SafeAreaView style={{flex:1, justifyContent:'center', alignItems:'center'}}>
      <Text style={{fontSize:24}}>ARKHE FIELD v7.2.0</Text>
      <View style={{marginTop:20}}>
        <Text>Φ_C: {phiC.toFixed(4)}</Text>
      </View>
    </SafeAreaView>
  );
};
export default App;
