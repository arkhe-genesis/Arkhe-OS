<?xml version="1.0" encoding="ISO-8859-1"?>
<!--
  Aplicativo Ginga Interativo: Contagem de Audiência Cross-Platform
  Exibe em tempo real os viewers do Twitch/YouTube das emissoras de TV aberta.

  Compatibilidade: TV 3.0 / DTV+ (perfil D), Ginga-NCL, ABNT NBR 15606-2
  Backend: ARKHE Audience Bridge API (porta 8054)
  Selo Canônico: 9033-C-001
-->
<ncl id="audience_app"
     xmlns="http://www.ncl.org.br/NCL3.0/EDTVProfile"
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xsi:schemaLocation="http://www.ncl.org.br/NCL3.0/EDTVProfile
                         http://www.ncl.org.br/NCL3.0/EDTVProfile.xsd">

  <!-- Cabeçalho da aplicação -->
  <head>
    <!-- Regiões da tela -->
    <regionBase>
      <!-- Barra inferior com audiência -->
      <region id="rgAudienceBar" left="0%" top="90%" width="100%" height="10%"
              zIndex="99">
        <region id="rgGlobo"    left="0%"   top="0%" width="20%" height="100%"/>
        <region id="rgSBT"      left="20%"  top="0%" width="20%" height="100%"/>
        <region id="rgRecord"   left="40%"  top="0%" width="20%" height="100%"/>
        <region id="rgBand"     left="60%"  top="0%" width="20%" height="100%"/>
        <region id="rgCultura"  left="80%"  top="0%" width="20%" height="100%"/>
      </region>
      <!-- Popup de detalhes (oculto por padrão) -->
      <region id="rgDetailPopup" left="60%" top="10%" width="35%" height="80%"
              zIndex="100"/>
    </regionBase>

    <!-- Descritores -->
    <descriptorBase>
      <descriptor id="dGlobo"    region="rgGlobo"    focusIndex="1"
                  moveUp="5" moveDown="2" moveLeft="5" moveRight="2"/>
      <descriptor id="dSBT"      region="rgSBT"      focusIndex="2"
                  moveUp="1" moveDown="3" moveLeft="1" moveRight="3"/>
      <descriptor id="dRecord"   region="rgRecord"   focusIndex="3"
                  moveUp="2" moveDown="4" moveLeft="2" moveRight="4"/>
      <descriptor id="dBand"     region="rgBand"     focusIndex="4"
                  moveUp="3" moveDown="5" moveLeft="3" moveRight="5"/>
      <descriptor id="dCultura"  region="rgCultura"  focusIndex="5"
                  moveUp="4" moveDown="1" moveLeft="4" moveRight="1"/>
      <descriptor id="dDetailPopup" region="rgDetailPopup" focusIndex="6"/>
    </descriptorBase>

    <!-- Conectores -->
    <connectorBase>
      <!-- Início da aplicação → carregar scripts Lua -->
      <causalConnector id="onBeginStartLua">
        <simpleCondition role="onBegin"/>
        <simpleAction role="start" max="unbounded" qualifier="par"/>
      </causalConnector>

      <!-- Timer: atualizar audiência periodicamente -->
      <causalConnector id="onTimerUpdate">
        <simpleCondition role="onTimer" key="updateTimer"/>
        <simpleAction role="start" max="unbounded" qualifier="par"/>
      </causalConnector>

      <!-- Tecla azul → mostrar/esconder detalhes -->
      <causalConnector id="onKeyBlueToggle">
        <simpleCondition role="onSelection" key="BLUE"/>
        <compoundAction operator="par">
          <simpleAction role="start"/>
          <simpleAction role="stop"/>
        </compoundAction>
      </causalConnector>

      <!-- Tecla vermelha → abrir link do Twitch -->
      <causalConnector id="onKeyRedOpenTwitch">
        <simpleCondition role="onSelection" key="RED"/>
        <simpleAction role="start"/>
      </causalConnector>

      <!-- Ao receber resultado da requisição HTTP -->
      <causalConnector id="onReceiveUpdate">
        <simpleCondition role="onEndAttribution"/>
        <simpleAction role="set" max="unbounded" qualifier="par"/>
      </causalConnector>
    </connectorBase>
  </head>

  <body>
    <!-- Porta de entrada: carrega o script Lua principal -->
    <port id="pEntry" component="luaAudience"/>

    <!-- Script Lua: orquestrador da aplicação -->
    <media id="luaAudience"
           src="audience_controller.lua"
           descriptor="dGlobo">
      <!-- Propriedades expostas para o NCL -->
      <property name="globoViewers"   value="0"/>
      <property name="sbtViewers"     value="0"/>
      <property name="recordViewers"  value="0"/>
      <property name="bandViewers"    value="0"/>
      <property name="culturaViewers" value="0"/>
      <property name="totalViewers"   value="0"/>
      <property name="lastUpdate"     value=""/>
    </media>

    <!-- Link 1: Ao iniciar, carregar dados de audiência -->
    <link id="lInit" xconnector="onBeginStartLua">
      <bind role="onBegin" component="luaAudience"/>
      <bind role="start"  component="luaAudience"/>
    </link>

    <!-- Link 2: Timer para atualização periódica (a cada 60s) -->
    <link id="lTimer" xconnector="onTimerUpdate">
      <bind role="onTimer" component="luaAudience">
        <bindParam name="updateTimer" value="60s"/>
      </bind>
      <bind role="start" component="luaAudience"/>
    </link>

    <!-- Mídias de texto para exibição dos números (overlay na barra) -->
    <media id="txtGlobo"    src="text_placeholder.lua" descriptor="dGlobo"/>
    <media id="txtSBT"      src="text_placeholder.lua" descriptor="dSBT"/>
    <media id="txtRecord"   src="text_placeholder.lua" descriptor="dRecord"/>
    <media id="txtBand"     src="text_placeholder.lua" descriptor="dBand"/>
    <media id="txtCultura"  src="text_placeholder.lua" descriptor="dCultura"/>

    <!-- Link 3: Atualizar textos quando dados chegarem -->
    <link id="lUpdateTexts" xconnector="onReceiveUpdate">
      <bind role="onEndAttribution" component="luaAudience"/>
      <bind role="set" component="txtGlobo"   interface="text">
        <bindParam name="var" value="$globoViewers"/>
      </bind>
      <bind role="set" component="txtSBT"     interface="text">
        <bindParam name="var" value="$sbtViewers"/>
      </bind>
      <bind role="set" component="txtRecord"  interface="text">
        <bindParam name="var" value="$recordViewers"/>
      </bind>
      <bind role="set" component="txtBand"    interface="text">
        <bindParam name="var" value="$bandViewers"/>
      </bind>
      <bind role="set" component="txtCultura" interface="text">
        <bindParam name="var" value="$culturaViewers"/>
      </bind>
    </link>

    <!-- Popup de detalhes (HTML5 via DTV Play ou Lua) -->
    <media id="detailPopup" src="detail_popup.lua" descriptor="dDetailPopup"/>

    <!-- Link 4: Tecla azul → mostrar popup de detalhes -->
    <link id="lBlueDetail" xconnector="onKeyBlueToggle">
      <bind role="onSelection" component="luaAudience" key="BLUE"/>
      <bind role="start"       component="detailPopup"/>
      <bind role="stop"        component="detailPopup"/>
    </link>
  </body>
</ncl>